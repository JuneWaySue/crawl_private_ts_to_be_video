# 导入相关包或模块
import threading, queue
import time, os, subprocess
import requests, urllib, parsel
import random, re
from Crypto.Cipher import AES
from selenium import webdriver

# 下载ts文件
def download_ts(urlQueue,aes,headers): 
    while True:
        try: 
            #不阻塞的读取队列数据 
            temp = urlQueue.get_nowait()
            url=temp[0]
            n=temp[1]
        except Exception as e:
            break
        response=requests.get(url,stream=True,headers=headers)
        ts_path = "./ts/%04d.ts"%n  # 注意这里的ts文件命名规则
        with open(ts_path,"wb+") as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    after=aes.decrypt(chunk)
                    file.write(after)
        print("%04d.ts OK..."%n)

if __name__ == '__main__':
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3741.400 QQBrowser/10.5.3863.400'}
    url='https://www.yueyuyy.com/tv/qumoshenyiyueyuban/'
    d=webdriver.Chrome()
    d.get(url)
    response=parsel.Selector(d.page_source)
    bofangye_url=urllib.parse.urljoin(url,response.xpath('//div[@class="playmenu"]/li/a/@href').get())
    d.get(bofangye_url)
    response=parsel.Selector(d.page_source)
    js_url=urllib.parse.urljoin(url,response.xpath('//div[@class="player_left"]/script/@src').get())
    d.get(js_url)
    response=d.page_source
    temp_url=[i.replace(i.split('/')[-1],'index.m3u8') for i in re.findall(',"(.*?)","m3u8"',response)]
    all_url=[]
    for i in temp_url:
        r=requests.get(i,headers=headers)
        time.sleep(0.2)
        all_url.append(urllib.parse.urljoin(i,r.text.strip().split('\n')[-1]))
    d.quit()
    
    # 下面开始循环下载所有剧集
    for num,url in enumerate(all_url):
        r=requests.get(url,headers=headers)
        urlQueue = queue.Queue()
        for i in r.text.split('\n'):
            if i.endswith('.ts'):
                urlQueue.put([urllib.parse.urljoin(url,i),urlQueue.qsize()])
            elif 'URI' in i:
                URI=urllib.parse.urljoin(url,re.findall('URI="(.*?)"',i)[0])
                key=requests.get(URI,headers=headers).text
                aes=AES.new(key,AES.MODE_CBC,key)
                
        # 下面开始多线程下载
        startTime = time.time()
        threads = []
        # 可以适当调节线程数,进而控制抓取速度
        threadNum = 4
        for i in range(threadNum):
            t = threading.Thread(target=download_ts, args=(urlQueue,aes,headers,))
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        endTime = time.time()
        print ('Done, Time cost: %s ' %  (endTime - startTime))
        
        # 下面是执行cmd命令来合成mp4视频
        command=r'copy/b D:\python3.7\HEHE\爬虫\ts\*.ts D:\python3.7\HEHE\爬虫\mp4\驱魔神医-第{0}集.mp4'.format(num+1)
        output=subprocess.getoutput(command)
        print('驱魔神医-第{0}集.mp4  OK...'.format(num+1))
        
        # 下面是把这一集所有的ts文件给删除
        file_list = []
        for root, dirs, files in os.walk('D:/python3.7/HEHE/爬虫/ts'):
            for fn in files:
                p = str(root+'/'+fn)
                file_list.append(p)
        for i in file_list:
            os.remove(i)
