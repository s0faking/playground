###############################################################
#                          HLS RIP                            #
###############################################################

# Requirements: mkvtoolnix ffmpeg
# usage: python hls_rip.py [playlist-url]
#
# Author: s0faking
 
import sys,urllib2,os,urllib
import os.path

tmp_dir = "tmp_video"
tmp_video_dir = tmp_dir+'/video'
tmp_audio_dir = tmp_dir+'/audio'
if len(sys.argv) < 2:
    sys.exit("usage: python hlc_rip.py [playlist-url]")
else:
    pls_url = str(sys.argv[1]).replace('\n', '')
    pls_filename = pls_url.split('/')[-1]
    base_url = pls_url.replace(pls_filename,'')
    video_base_url = base_url.replace("m3u8s/",'')
    print "VIDEO BASE URL: "+video_base_url

    resolution_choice = "1920x1080"
    audio_quality_choice = "audio-stereo-hi"

    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (Linux; Android 4.4.2; Nexus 10 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.93 Safari/537.36')]

    print "Loading from "+base_url+"\n"



def getBasePls():
    audiostream = ""
    videostream = ""
    response = opener.open(pls_url)
    data = response.readlines()
    resolution_arr = chooseResolution()
    print "Choose the resolution [0-%d]:" % (len(resolution_arr)-1)
    resolution_choice = raw_input()
    resolution_choice = resolution_arr[int(resolution_choice)]
    print "Your choice: "+ resolution_choice
    audio_quality_arr = chooseAudioQuality()
    print "Choose the audio quality [0-%d]:" % (len(audio_quality_arr)-1)
    audio_quality_choice = raw_input()
    audio_quality_choice = audio_quality_arr[int(audio_quality_choice)]
    print "Your choice: "+ audio_quality_choice
    
    
    read_next_val = False
    for line in data:
        if read_next_val:
            if line != "":
                videostream = line.replace('\n', '')
                read_next_val = False
        if '#EXT-X-MEDIA:TYPE=AUDIO' in line:
            if 'GROUP-ID="%s"' % audio_quality_choice in line:
                linearray = line.split(',')
                for val in linearray:
                    if 'URI=' in val:
                        audiostream = val.replace('URI="','').replace('"',"").replace('\n', '');
                            
        if '#EXT-X-STREAM-INF' in line:
            if 'RESOLUTION=%s' % resolution_choice in line:
                read_next_val = True
    createTmpDirs()   
    if videostream and audiostream:
        videostream = base_url+videostream
        audiostream = base_url+audiostream
        print "Loading Video: "+videostream
        downloadAudioVideoTS(videostream,tmp_video_dir)
    
        print "Audio: "+audiostream
        downloadAudioVideoTS(audiostream,tmp_audio_dir)
        
        processVideos()
    else:
        print "Sorry - No 1080p Content found"


def chooseResolution():
    tmp_response = opener.open(pls_url)
    tmp_data = tmp_response.readlines()
    tmp_resolution_count = 0
    
    resolution_arr = []
    
    for line in tmp_data:
        if '#EXT-X-STREAM-INF' in line:
            linearray = line.split(',')
            for val in linearray:
                if 'RESOLUTION=' in val:
                    resolution = val.replace('RESOLUTION=','').replace('"',"").replace('\n', '');
                    print "(%d) %s" % (tmp_resolution_count , resolution)
                    tmp_resolution_count = tmp_resolution_count + 1
                    resolution_arr.append(resolution)
    return resolution_arr
        
        
def chooseAudioQuality():
    tmp_response = opener.open(pls_url)
    tmp_data = tmp_response.readlines()
    tmp_audio_count = 0
    
    audio_arr = []
    
    for line in tmp_data:
        if '#EXT-X-MEDIA:TYPE=AUDIO' in line:
            linearray = line.split(',')
            for val in linearray:
                if 'GROUP-ID=' in val:
                    audio_quality = val.replace('GROUP-ID="','').replace('"',"").replace('\n', '');
                    print "(%d) %s" % (tmp_audio_count , audio_quality)
                    tmp_audio_count = tmp_audio_count + 1
                    audio_arr.append(audio_quality)
    return audio_arr
        
def processVideos():
    mergeVideoCMD = "cat %s/*.ts > video.ts" % tmp_video_dir
    mergeAudioCMD = "cat %s/*.ts > audio.ts" % tmp_audio_dir
    demuxVideoCMD = "mkvmerge -o video.mkv video.ts"
    demuxAudioCMD = "mkvmerge -o audio.mkv audio.ts"
    extractAacCMD = "mkvextract tracks audio.mkv 0:audio.aac"
    extractAacCMD2 = "mkvextract tracks audio.mkv 1:audio.aac"
    concatCMD = "ffmpeg -i video.mkv -i audio.aac -acodec copy -vcodec copy final_video.mkv"
    
    if not os.path.isfile("video.ts"):
        print "Merging Video Files ..."
        os.system(mergeVideoCMD)
    if not os.path.isfile("audio.ts"):
        print "Merging Audio Files ..."
        os.system(mergeAudioCMD)
    if not os.path.isfile("video.mkv"):
        print "Demuxing Video Files ..."
        os.system(demuxVideoCMD)
    if not os.path.isfile("audio.mkv"):
        print "Demuxing Audio Files ..."
        os.system(demuxAudioCMD)    
    if not os.path.isfile("audio.aac"):
        print "Extracting AAC Audio ..."
        output = os.system(extractAacCMD)
        if str(output) != '0':
            os.system(extractAacCMD2)
    if not os.path.isfile("final_video.mkv"):
        print "Merging Final Video ..."
        os.system(concatCMD)
    
    
    
def downloadAudioVideoTS(url,target_dir):
    audio_video_response = opener.open(url)
    print "Video File Playlist URL: "+url
    audio_video_data = audio_video_response.readlines()
    count = 0
    for line in audio_video_data:
        if line.startswith('http://') or line.startswith('../video/') or line.startswith('../audio/'):
            tmp_file = line.replace('\n','')
            tmp_file = tmp_file.replace("../","")
            tmp_file = video_base_url + tmp_file
            
            
            tmp_name = tmp_file.split('/')[-1]
            tmp_filename = target_dir+"/"+str(count).zfill(5)+".ts"
            print "file: "+tmp_file
            print "name: "+tmp_name
            if not os.path.isfile(tmp_filename):
                print "Downloading to "+tmp_filename
                urllib.urlretrieve(tmp_file,tmp_filename)
            count = count + 1
    print "Found "+str(count)+" Entries"
    
def createTmpDirs():
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
        
    if not os.path.exists(tmp_video_dir):
        os.makedirs(tmp_video_dir)
        
    if not os.path.exists(tmp_audio_dir):
        os.makedirs(tmp_audio_dir)
        
def removeProjectFiles():
    choice = ""
    print "Do you want to delete the Project Files? (Y/N)"
    choice = str(raw_input()).lower()
    if choice == 'y':
        os.remove('video.ts')
        os.remove('video.mkv')
        os.remove('audio.ts')
        os.remove('audio.aac')
        os.remove('audio.mkv')
    else:
        print "Project Files not removed ..."
    choice = ""
    print "Do you want to delete the Source TS Files? (Y/N)"
    choice = str(raw_input()).lower()
    if choice == 'y':  
        os.removedirs(tmp_dir)
    else:
        print "Source Files not removed ..."
        
        
getBasePls()
removeProjectFiles()

