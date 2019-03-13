import re
from bs4 import BeautifulSoup
import requests
from requests.exceptions import RequestException
import csv


# url请求
def get_one_page(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        return None


# journal_html拆分块
def divide_html(achar, str):

    str = str.strip()
    ret = []
    for ind in range(len(achar)):
        pos = str.index(achar[ind])
        ret.append(str[:pos])
        str = str[pos + 1:]
    ret.append(str)
    return ret


# 解析期刊首页
def parse_journal_page(html):
    # request a root dictionary of journal
    pos1 = html.index('期刊论文列表')
    pos2 = html.index('Copyright')
    list_html = html[pos1:pos2]
    init_soup = BeautifulSoup(list_html, 'lxml')
    for tag_a in init_soup.select('a'):
        href = 'http://cdblp.ruc.edu.cn' + tag_a.get('href')
        j_html = get_one_page(href)
        parse_journal_subpage(j_html)
        #
        # 延时块
        # print('5s后继续获取……\n----------------------')
        # time.sleep(5)




# 解析文章页
def parse_article(url):
    a_html = get_one_page(url)
    pos1 = a_html.index('单位')
    pos2 = a_html.index('正文快照')
    a_html = a_html[pos1:pos2]
    soup_html = BeautifulSoup(a_html, 'lxml')
    main_info = soup_html.findAll(name='td')

    # print(main_info[10].string)

    # main_info[0]  - organization
    # main_info[2]  - keywords
    # main_info[6]  - foundation
    # main_info[10] - abstract
    info = {
        'Organization': main_info[0].string,
        'Keywords': main_info[2].string,
        'Source': main_info[4].string,
        'Foundation': main_info[6].string,
        'Abstract': main_info[10].string
    }
    return info


# 解析期刊每一期的详情页
def parse_journal_subpage(html):
    # 存储论文信息，作为返回值
    article_set = []
    try:
        # request a sub-site of journal
        pos1 = html.index('论文列表')
        pos2 = html.index('Copyright')
        list_html = html[pos1:pos2]
        soup_html = BeautifulSoup(list_html, 'lxml')
        article = []
        # print(soup_html)
        article_list_html = soup_html.findAll(name='td', attrs={'class': '', 'colspan': ''})
    except:
        return article_set
    # 遍历每一条信息，即一篇文章
    for an_article_html in article_list_html:
        pre_html = str(an_article_html)[4:-5]
        div_item = ''.join(pre_html.split('.html'))
        # print(div_item)
        try:
            div_item = divide_html(['.', '.', ',', ',', ':'], div_item)
        except:
            continue

        # print(div_item)
        # author - div_item[0]
        # article - div_item[1]
        # journal - div_item[2]
        # year - div_item[3]
        # phase - div_item[4]
        # pages - div_item[5]

        # 获取文章名
        article = ''
        try:
            t_html = BeautifulSoup(div_item[1], 'lxml')
            article_html = t_html.find('a')
            article += str(article_html.string)
            article_index = re.search('.*?href="(.*?)"', div_item[1])
            article_url = 'http://cdblp.ruc.edu.cn' + str(article_index.group(1)) + '.html'
            # print(article_url)
            # 此处传回文章的相关信息-dict类型
            article_part_info = parse_article(article_url)
            article_part_info['Source'] = ''.join(article_part_info['Source'].split())
        except:
            print('获取文章名错误（正常）\n----------------------')
            continue

        # 获取期刊名
        journal_name = ''
        try:
            t_html = BeautifulSoup(div_item[2], 'lxml')
            journal_html = t_html.find('a')
            journal_name += str(journal_html.string)
        except:
            print("获取期刊名称错误\n----------------------")
            continue

        # 获取该文章的绝对ID编号（用于数据存储）
        global article_id_count

        article_id = journal_id[journal_ind] + str(article_id_count)

        author_name_set = ''

        try:
            t_html = BeautifulSoup(div_item[0], 'lxml')
            author_html = t_html.findAll('a')
            for author_name in author_html:
                # 遍历每个作者的个人信息站点
                # author_ID = get_author_info(str(author_name.string), article)
                author_name_set += (str(author_name.string) + ' ')
        except:
            print('获取作者信息错误\n----------------------')
            continue

        # 获取文章的发表年份
        year_of_article = div_item[3].strip()

        # 获取文章所在的期数
        phase = ''
        try:
            t_html = BeautifulSoup(div_item[4], 'lxml')
            phase_html = t_html.findAll('a')
            phase += str(phase_html[1].string)
            phase = phase.strip('()')
        except:
            print("获取文章期数错误\n----------------------")
            continue

        # 获取文章所在页数
        pages_of_article = div_item[5].strip()

        # 数据整合
        article_info = {
            'Article_ID': article_id,
            'Name': article,
            'Author': author_name_set,
            'Organization': str(article_part_info['Organization']).strip().replace('\n',''),
            'Keywords': str(article_part_info['Keywords']).strip().replace('\n',''),
            # 'Source': article_part_info['Source'],
            'Journal': journal_name,
            'Year': year_of_article,
            'Phase': phase,
            'Pages': pages_of_article,
            'Found': str(article_part_info['Foundation']).strip().replace('\n','').replace(' ','').replace('~',''),
            'Abstract': str(article_part_info['Abstract']).strip().replace('\n','')
        }
        # print(article_info)
        print(article_info['Article_ID'], article_info['Name'], article_info['Abstract'])
        article_set.append(article_info)
        article_id_count = article_id_count + 1
        print('----------------------')

    # 存储本期文章数据
    save_file(article_set)
    print('！！！！！！存储单期成功！！！！！！')


def save_file(article_set):
    # 存储文章信息
    global csv_header_flag
    with open('article_data_1.csv', 'a', encoding='utf_8_sig') as csvfile:
        fieldnames = ['Article_ID', 'Name', 'Author', 'Organization', 'Keywords', 'Journal', 'Year', 'Phase', 'Pages', 'Found',
                      'Abstract']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if csv_header_flag == 0:
            writer.writeheader()
            csv_header_flag = 1
        writer.writerows(article_set)



# 期刊集
journal_name_set = ['软件学报','计算机学报','计算机研究与发展','中国图象图形学报','中文信息学报','计算机科学','小型微型计算机系统',
                    '计算机科学与探索','计算机辅助设计与图形学学报','中国科学F辑','电子学报','计算机工程与科学']

# 期刊id编号
journal_id = ['000','001','002','003','004','005','006','007','008','009','010','011']

# 文章相对ID编号
# (文章的绝对编号为"期刊编号+文章相对编号")
article_id_count = 1

# 文章爬取序号，选择期刊集中的期刊（0，1，2）
journal_ind = 0

# csv文件 header是否已经填充，初始为未填充状态
csv_header_flag = 0


# 主函数
def main():
    global article_id_count
    global journal_ind
    for ind in range(len(journal_name_set)):
        journal_ind = ind
        # 期刊URL
        url = 'http://cdblp.ruc.edu.cn/computer/journal/' + journal_name_set[journal_ind]
        # 获取期刊首页的html
        j_html = get_one_page(url)
        # 解析期刊，并存储
        parse_journal_page(j_html)
        # 文章序号归1
        article_id_count = 1
        print('开始爬取下一个期刊\_____________')


if __name__ == '__main__':
    main()
