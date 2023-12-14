import streamlit as st
import requests as r
import re
import urllib.parse
from tqdm import tqdm
def song_data(name:str):
    '''Function to get info of given song from jiosavaan'''
    url="https://www.jiosaavn.com/api.php?__call=autocomplete.get&query="+name+"&_format=json&_marker=0&ctx=wap6dot0"
    resp=r.get(url).text
    info = re.findall(r'songs\":{\"data\":\[(.*?)\]',resp)[0]
    data = re.findall(r'id\":\"(.*?)\".*?:\"(.*?)\".*?url\":\"(.*?)\".*?description\":\"(.*?)\"',info)
    return data

def get_dl(link):
    song_id = re.findall(r'song/(.*?)/(.*)',link)[0]
    # Get direct download link of song from savaan server
    url = f'https://www.jiosaavn.com/api.php?__call=webapi.get&api_version=4&_format=json&_marker=0&ctx=wap6dot0&token={song_id[1]}&type=song'
    resp = r.get(url)
    response = resp.json()
    final_url = urllib.parse.quote(response['songs'][0]['more_info']['encrypted_media_url'])
    dwn_url = f'https://www.jiosaavn.com/api.php?__call=song.generateAuthToken&url={final_url}&bitrate=320&api_version=4&_format=json&ctx=wap6dot0&_marker=0'
    dwn_r = r.get(dwn_url)
    dl_lnk = re.findall(r"(.+?(?=Expires))",dwn_r.json()['auth_url'])[0].replace('.cf.','.').replace('?','').replace('ac','aac')
    dl_items = [dl_lnk, song_id[0]]
    return dl_items

def download_mp3(link, progress_bar):
    try:
        response = r.get(link, stream=True)

        # Get the total file size in bytes
        total_size = int(response.headers.get('content-length', 0))
        content = b""
        with tqdm(
            desc="Downloading",
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                size = len(data)
                content += data
                bar.update(size)
                progress_bar.progress(bar.n / bar.total)

        return content
    except Exception as e:
        st.error(f"Error: {e}")

st.title(":red[Song Downloader]")
st.subheader(":green[Easily download your favourite songs in highest quality(320kbps)]")
name = st.text_input('Enter song name')
titles = []
description = []
urls = []

if "urls" not in st.session_state:
    st.session_state["urls"] = None

if 'Download' not in st.session_state:
    st.session_state['Download'] = False

if st.button('Done'):
    a =  song_data(name)
    for i in a:
        titles.append(i[1])
        urls.append(i[2].replace("\\/","/"))
        description.append(i[3].replace("\\u00b7",""))
    st.write('Available results are: ')    # Show the available results to user and ask for user's choice
    for i in range(len(titles)):
        st.text(f'{i+1}. {titles[i]} : {description[i]}')
    st.session_state["urls"]=urls

num = st.number_input("Enter index of song to download", value=None, max_value=3)

if st.button("Download"):
    url = st.session_state["urls"]
    lnk = url[int(num)-1]
    down = get_dl(lnk)
    st.write(":green[Downloading....]")
    progress_bar = st.progress(0)
    content=download_mp3(down[0], progress_bar)
    st.success("Downloaded successfully!")
    st.download_button(label="Save Audio File", data=content, key="audio_file", file_name=f"{down[1]}.mp3", mime='audio/mp3')