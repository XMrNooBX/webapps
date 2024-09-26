import streamlit as st
import requests as r
from pytubefix import YouTube as yt
import re
import urllib.parse
from io import BytesIO

st.markdown(""" 
    <style>
    body {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: #fff;
        font-family: 'Courier New', Courier, monospace;
    }
    .stButton>button {
        background-color: #66e862 !important;
        color: #4d0e0e !important;
        border-radius: 10px;
        padding: 10px 20px;
        font-size: 16px;
    }
    .stProgress {
        background-color: #cb13cd !important;
    }
    .stTextInput>div>input {
        background-color: #ee1d3c;
        color: white;
        border-radius: 8px;
        padding: 8px;
    }
    .stRadio>div>label>div {
        color: #d0a8f4 !important;
    }
    h1 {
        text-shadow: 2px 2px #4ea2e8;
        animation: flicker 2.5s infinite alternate;
    }
    .highlight {
        font-size: 20px; 
        color: #2bdfdc;
        text-decoration: underline; 
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.6); /* Adding shadow */
    }
    .highlight-youtube {
        font-size: 20px;  
        color: #ff0016;   
        text-decoration: underline; 
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.6); /* Adding shadow */
    }
    @keyframes flicker {
        0% {opacity: 1;}
        50% {opacity: 0.8;}
        100% {opacity: 1;}
    }
    </style>
""", unsafe_allow_html=True)

def song_data(name: str):
    results = {}
    url = f"https://www.jiosaavn.com/api.php?__call=autocomplete.get&query={name}&_format=json&_marker=0&ctx=wap6dot0"
    info = r.get(url)
    if info.status_code == 200:
        resp = info.json().get("songs", {}).get("data", [])
        for i in resp:
            results[f"{i['title']} - {i['description']}"] = i['url']
    return results

def get_dl(link):
    try:
        song_id = re.findall(r'song/(.*?)/(.*)', link)[0]
        url = f'https://www.jiosaavn.com/api.php?__call=webapi.get&api_version=4&_format=json&_marker=0&ctx=wap6dot0&token={song_id[1]}&type=song'
        resp = r.get(url)
        response = resp.json()
        final_url = urllib.parse.quote(response['songs'][0]['more_info']['encrypted_media_url'])
        dwn_url = f'https://www.jiosaavn.com/api.php?__call=song.generateAuthToken&url={final_url}&bitrate=320&api_version=4&_format=json&ctx=wap6dot0'
        dwn_r = r.get(dwn_url)
        dl_lnk = re.findall(r"(.+?(?=Expires))", dwn_r.json()['auth_url'])[0].replace('.cf.', '.').replace('?', '').replace('ac', 'aac')
        dl_items = [dl_lnk, song_id[0]]
        return dl_items
    except Exception as e:
        st.error(f"🚨 Error fetching download link: {e}")
        return None, None

def get_yt_results(query: str):
    query = query.replace(' ', '+')
    url = f'https://www.youtube.com/results?search_query={query}'
    response = r.get(url).text
    resp = re.findall(r'videoId\":\"(.*?)\"', response)
    
    if len(resp) > 0:
        v_ids = list(dict.fromkeys(resp))[:5]
        songs = {}
        for i in v_ids:
            lnk = f'https://www.youtube.com/watch?v={i}'
            video = yt(lnk)

            if video.length > 60:
                songs[video.title] = lnk
        return songs
    else:
        st.error("😶 Kuch nai mila")
        return {}

def on_progress_callback(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = int(bytes_downloaded / total_size * 100)
    st.session_state.progress_bar.progress(percentage_of_completion)

def download(url):
    if 'youtube.com' in url:
        try:
            yt_video = yt(url, on_progress_callback=on_progress_callback)
            chc = yt_video.streams.filter(only_audio=True)[-1]
            titl = yt_video.title
            buffer = BytesIO()
            st.session_state.progress_bar = st.progress(0)
            chc.stream_to_buffer(buffer)
            buffer.seek(0)
            return buffer, titl
        except Exception as e:
            st.error("😕 ye nai ho paega. Koi aur option Try kya ya naam me kuch add kr k dekh")
            return None, None
    else:
        try:
            response = r.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            content = b""
            bytes_downloaded = 0
            chunk_size = 1024
            st.session_state.progress_bar = st.progress(0)
            for data in response.iter_content(chunk_size=chunk_size):
                content += data
                bytes_downloaded += len(data)
                progress = bytes_downloaded / total_size
                st.session_state.progress_bar.progress(progress)
            return content, "JioSaavn_Song"
        except Exception as e:
            st.error(f"🥺 Sorry yaar. Firse try kr na")
            return None, None

if "jio_songs" not in st.session_state:
    st.session_state.jio_songs = {}
if "yt_songs" not in st.session_state:
    st.session_state.yt_songs = {}
if "last_searched_song" not in st.session_state:
    st.session_state.last_searched_song = ""
if "yt_refresh_trigger" not in st.session_state:
    st.session_state.yt_refresh_trigger = False

st.title("🐈 :red[Meow-sic Downloader]")
st.subheader("🎧 :green[Your purrfect tunes, just a click away!]")

song = st.text_input(':red[🎵 Gaane ka naam bta]')

if song:
    if st.session_state.last_searched_song != song:
        st.session_state.jio_songs = song_data(song)
        st.session_state.last_searched_song = song
        st.session_state.yt_songs = {}
        st.session_state.yt_refresh_trigger = False
    
    jio_titles = list(st.session_state.jio_songs.keys()) + ["😒 Aur Kuch dikha"]

    st.markdown('<span class="highlight">Kon sa Download karu:</span>', unsafe_allow_html=True)

    selected_jio_song = st.radio('Choose kr: ', jio_titles, key="selected_jio_song")

    if selected_jio_song != "😒 Aur Kuch dikha":
        if st.button('✔️ Ye wala'):
            url = st.session_state.jio_songs.get(selected_jio_song)
            dl_link, title = get_dl(url)
            if dl_link:
                song_content, song_title = download(dl_link)
                if song_content:
                    st.download_button(
                        label="😏 Download",
                        data=song_content,
                        file_name=f"{title}.mp3",
                        mime="audio/mpeg"
                    )
    else:
        if st.button("🔍 Ye wala"):
            st.session_state.yt_songs = get_yt_results(song)
            st.session_state.yt_refresh_trigger = True

        if st.session_state.yt_refresh_trigger:
            if st.session_state.yt_songs:
                st.markdown('<span class="highlight-youtube">Le Yaar:</span>', unsafe_allow_html=True)
                yt_choice = st.radio('Choose kr: ', list(st.session_state.yt_songs.keys()))

                if st.button('🚀 Ye wala'):
                    selected_url = st.session_state.yt_songs[yt_choice]
                    song_content, song_title = download(selected_url)

                    if song_content:
                        st.download_button(
                            label="😏 Download",
                            data=song_content,
                            file_name=f"{song_title}.mp3",
                            mime="audio/mpeg"
                        )
            else:
                st.error("😶 Kuch nai mila")

