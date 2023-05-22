import os
import requests
import json
from urllib.parse import quote
import string
import time

active_source = 0

def search_videos(source,word,pg = 1,log=True):
    url = source+'?ac=videolist&wd='+quote(word, safe = string.printable)+'&pg='+str(pg)
    if log:print('正在连接:',url,end='\r')
    try:
        r = requests.get(url,timeout=10)
        datas = json.loads(r.text.replace('\n',''))
    except:
        if log:print('\033[31m资源无法连接\033[0m')
        return None
    res = {}
    res['page'] = datas['page']
    res['page_num'] = datas['pagecount']
    res['total'] = datas['total']
    videos = []
    if res['total'] != 0:
        for l in datas['list']:
            video = {'name':l['vod_name']}
            video['pic'] = l['vod_pic']
            _links = {}
            if l['vod_play_note'] and l['vod_play_note'] in l['vod_play_url']:
                for link in l['vod_play_url'].split(l['vod_play_note'])[1].split('#'):
                    if link == '':continue
                    _lk = link.split('$')
                    if not '.m3u8' in _lk[1]:continue
                    _links[_lk[0]] = _lk[1]
            else:
                for link in l['vod_play_url'].split('#'):
                    if link == '':continue
                    _lk = link.split('$')
                    if not '.m3u8' in _lk[1]:continue
                    _links[_lk[0]] = _lk[1]
            if _links == {}:continue
            video['links'] = _links
            videos.append(video)
        if len(videos) == 0:return None
    else:return None
    res['videos'] = videos.copy()
    return res

def search_all(source,word,pg = 1):
    length = len(source.keys())
    res = {'page':1,'page_num':1,'videos':[]}
    for i,k in enumerate(source.keys()):
        print('正在搜索 \033[33;3m第'+str(i+1)+'个 共'+str(length)+'个\033[0m : '+k+'...',end='\r')
        ret = search_videos(source[k],word,pg,log=False)
        if not ret:continue
        for i in range(len(ret['videos'])):ret['videos'][i]['name']+='_$from:'+k
        res['videos'] += ret['videos'].copy()
        time.sleep(0.25) #0.1 Kun
    res['total'] = len(res['videos'])
    return res

def load_source():
    global sources,source_name,active_source
    active_source = 0
    with open('source.json','r',encoding='utf-8') as g:
        sources = json.loads(g.read())
    source_name = [''] + list(sources.keys())
    return source_name,sources

def download(video):
    #print(video)
    dlid = str(round(id(video)*114514-time.time()*1919810))[:16]
    grand = open('./._download_'+dlid+'.bat','w',encoding='gbk')
    video_name = video['name']
    for i in ['/','\\',':','*','?','"','|','<','>']:video_name = video_name.replace(i,'_')
    for link in video['links'].keys():
        grand.write('.\\m3u8DL\\m3u8DL.exe '+video['links'][link]+' --saveName "'+video_name+'_'+link+'" --enableDelAfterDone --disableIntegrityCheck\n')
    grand.close()
    time.sleep(0.1)
    print('\033[33m下载开始\033[0m ID:'+dlid)
    print('\033[2m如果下载没有正常开始,请双击运行: "._download_'+dlid+'.bat"\033[0m')
    os.system('start "" "._download_'+dlid+'.bat"')

def tui():
    global active_source,source_name,width
    width = os.get_terminal_size().columns
    os.system('cls')
    print('\033[33m'+'-'*(width//2-5)+'视频下载器'+'-'*(width//2-5)+'\033[0m')
    info = '\033[2m-- 输入: ">?" 寻求帮助 --\033[0m'
    print(' '*round((width-len(info))//2)+info)

def change_active():
    global active_source,width
    tui()
    print('\033[1m请选择视频源:\033[0m')
    print('    \033[36m(0) \033[33m搜索全部可用源 \033[2m(default较慢)\033[0m')
    if len(source_name) > 1:
        for i,n in enumerate(source_name[1:]):print('    \033[36m('+str(i+1)+') \033[0m'+n)
    ans = input('> \033[2;3m输入纯数字编号或视频源名称\033[0m'+'\b'*26)
    if ans.isdigit() and 0 <= int(ans)< len(source_name):active_source = int(ans)
    elif ans in source_name:active_source = source_name.index(ans)
    elif ans == '搜索全部可用源':pass
    else:print('\033[31m输入不规范\033[0m')

def search(args=None):
    global width
    tui()

    page = 1
    if args:
        print('\033[32m'+source_name[active_source]+'\033[0m> 搜索 : ')
        word = args[0]
        page = args[1]
    else:word = input('\033[32m'+source_name[active_source]+'\033[0m> 搜索 : \033[2;3m搜索视频名称\033[0m'+'\b'*12)

    print('searching...',end='\r')
    if active_source == 0:video_dic = search_all(sources,word)
    else:video_dic = search_videos(sources[source_name[active_source]],word,page)
    print(' '*(width-1),end='\r')
    if video_dic is None:
        print('\033[31m未搜索到视频\033[0m')
        return 1
    print('搜素完毕,共搜索到\033[1m'+str(video_dic['total'])+'\033[0m个结果:')
    
    names = []
    for i,v in enumerate(video_dic['videos']):
        if '_$from:' in v['name']:
            _ = v['name'].split('_$from:')
            v['name'] = _[0]
            print('    \033[36m('+str(i)+') \033[0m'+v['name']+'  \033[2m(from:'+_[1]+')\033[0m')
        else:print('    \033[36m('+str(i)+') \033[0m'+v['name'])
        names.append(v['name'])
    pg_name = '\033[33;1m( 第'+str(video_dic['page'])+'页 / 共'+str(video_dic['page_num'])+'页 )\033[0m'
    print(' '*abs(width-len(pg_name)-10)+pg_name)
    ans = input('> \033[2;3m输入纯数字编号或视频名称,"<"上一页,">"下一页,":n"跳转至第n页\033[0m'+'\b'*60)

    active_video = 0
    if ans.isdigit() and 0 <= int(ans)< len(names):active_video = video_dic['videos'][int(ans)]
    elif ans == '':
        print('\033[31m退出搜索\033[0m')
        return 1
    elif ans in names:active_video = video_dic['videos'][names.index(ans)]
    elif ans == '>':
        page += 1
        if page >= video_dic['page_num']:page = 1
        search([word,page])
    elif ans == '<':
        page -= 1
        if page < 1:page = video_dic['page_num']
        search([word,page])
    elif len(ans) > 1 and ans[0] == ':'and ans[1:].isdigit() and 1 <= int(ans[1:]) <= video_dic['page_num']:
        page = int(ans[1:])
        search([word,page])
    else:
        print('\033[31m输入不规范\033[0m')
        return 1
    print('\033[1m'+active_video['name']+'\033[0m> 的分集目录:')
    video_names = []
    for i,n in enumerate(active_video['links'].keys()):
        print('    \033[36m('+str(i)+') \033[0m'+n)
        video_names.append(n)
    ans = input('> \033[2;3m输入需要下载的数字编号组,如:"0,1,4","1-3,5",不输入默认全部下载\033[0m'+'\b'*62)
    if ans == '':download(active_video)
    else:
        try:
            dl_list = {}
            for i in ans.split(','):
                if '-' in i:
                    _ = i.split('-')
                    assert _[0].isdigit()
                    assert _[1].isdigit()
                    assert 0 <= int(_[0]) < len(video_names)
                    assert (0 <= int(_[1]) < len(video_names))
                    for n in range(int(_[0]),int(_[1])+1):dl_list[video_names[n]] = active_video['links'][video_names[n]]
                elif i.isdigit() and 0 <= int(i) < len(video_names):dl_list[video_names[int(i)]] = active_video['links'][video_names[int(i)]]
        except:
            print('\033[31m输入不规范\033[0m')
            return 1
        active_video['links'] = dl_list
        download(active_video)
    return [word,page]

def cmd(ret):
    ans = input('> \033[2;3m按下回车重新搜索或执行其他命令\033[0m'+'\b'*30)
    if ans == '>?':
        print('    \033[1m>C\033[0m 改变视频源')
        print('    \033[1m>R\033[0m 重新加载视频源')
        print('    \033[1m>S\033[0m 回到刚刚的搜索结果')
        print('    \033[1m>O\033[0m 打开下载文件所在目录')
        print('    \033[1m>?\033[0m 寻求帮助')
        cmd(ret)
    elif ans == '>C':change_active()
    elif ans == '>R':
        load_source()
        change_active()
    elif ans == '>S':search(ret)
    elif ans == '>O':
        os.system('start "" "./Download"')
        cmd(ret)

load_source()

change_active()

while True:
    ret = search()
    cmd(ret)
