import subprocess



def convert480p(source, new_file_name:str):
    cmd = 'ffmpeg -i "{}" -s hd480 -c:v libx264 -crf 23 -c:a aac -strict -2 "{}"'.format(source, new_file_name)
    run = subprocess.run(cmd, capture_output=True, shell=True)

def convert720p(source, new_file_name:str):
    cmd = 'ffmpeg -i "{}" -s hd720 -c:v libx264 -crf 23 -c:a aac -strict -2 "{}"'.format(source, new_file_name)
    run = subprocess.run(cmd, capture_output=True, shell=True)

def convert1080p(source, new_file_name:str):
    cmd = 'ffmpeg -i "{}" -s hd1080 -c:v libx264 -crf 23 -c:a aac -strict -2 "{}"'.format(source, new_file_name)
    run = subprocess.run(cmd, capture_output=True, shell=True)

