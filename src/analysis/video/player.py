__author__ = 'chivers'

from moviepy.video.io.VideoFileClip import VideoFileClip as vfc
from moviepy.video.io.preview import show as showVideo,preview as previewVideo
from moviepy.audio.io.preview import preview as previewSound


from moviepy.config import get_setting
from moviepy.tools import cvsecs

import subprocess as sp
import re
import os
try:
    from subprocess import DEVNULL  # py3k
except ImportError:
    DEVNULL = open(os.devnull, 'wb')

import pygame
import sys
import getopt
import matplotlib.pyplot as plt
import numpy as np

class mursClip:

    def __init__(self,mp4File):

        self.fName = mp4File
        self.info = self.ffmpeg_parse_infos(mp4File)
        print self.info
        self.clip = vfc(mp4File,audio=True)

    def playAudioClip(self,t1,t2):
        aclip = self.clip.subclip(t_start=t1,t_end=t2)
        previewSound(aclip.audio,fps=self.info['audio_fps'])

    def ffmpeg_parse_infos(self,filename, print_infos=False, check_duration=True):
        """Get file infos using ffmpeg.
        Returns a dictionnary with the fields:
        "video_found", "video_fps", "duration", "video_nframes",
        "video_duration", "audio_found", "audio_fps"
        "video_duration" is slightly smaller than "duration" to avoid
        fetching the uncomplete frames at the end, which raises an error.
        """


        # open the file in a pipe, provoke an error, read output
        is_GIF = filename.endswith('.gif')
        cmd = [get_setting("FFMPEG_BINARY"), "-i", filename]
        if is_GIF:
            cmd += ["-f", "null", "/dev/null"]

        popen_params = {"bufsize": 10**5,
                        "stdout": sp.PIPE,
                        "stderr": sp.PIPE,
                        "stdin": DEVNULL}

        if os.name == "nt":
            popen_params["creationflags"] = 0x08000000

        proc = sp.Popen(cmd, **popen_params)

        proc.stdout.readline()
        proc.terminate()
        infos = proc.stderr.read().decode('utf8')
        del proc

        if print_infos:
            # print the whole info text returned by FFMPEG
            print( infos )


        lines = infos.splitlines()
        if "No such file or directory" in lines[-1]:
            raise IOError(("MoviePy error: the file %s could not be found !\n"
                          "Please check that you entered the correct "
                          "path.")%filename)

        result = dict()


        # get duration (in seconds)
        result['duration'] = None

        if check_duration:
            try:
                keyword = ('frame=' if is_GIF else 'Duration: ')
                line = [l for l in lines if keyword in l][0]
                match = re.findall("([0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9])", line)[0]
                result['duration'] = cvsecs(match)
            except:
                raise IOError(("MoviePy error: failed to read the duration of file %s.\n"
                               "Here are the file infos returned by ffmpeg:\n\n%s")%(
                                  filename, infos))

        # get the output line that speaks about video
        lines_video = [l for l in lines if ' Video: ' in l and re.search('\d+x\d+', l)]

        result['video_found'] = ( lines_video != [] )

        if result['video_found']:


            try:
                line = lines_video[0]

                # get the size, of the form 460x320 (w x h)
                match = re.search(" [0-9]*x[0-9]*(,| )", line)
                s = list(map(int, line[match.start():match.end()-1].split('x')))
                result['video_size'] = s
            except:
                raise IOError(("MoviePy error: failed to read video dimensions in file %s.\n"
                               "Here are the file infos returned by ffmpeg:\n\n%s")%(
                                  filename, infos))


            # get the frame rate. Sometimes it's 'tbr', sometimes 'fps', sometimes
            # tbc, and sometimes tbc/2...
            # Current policy: Trust tbr first, then fps. If result is near from x*1000/1001
            # where x is 23,24,25,50, replace by x*1000/1001 (very common case for the fps).

            try:
                match = re.search("( [0-9]*.| )[0-9]* tbr", line)
                tbr = float(line[match.start():match.end()].split(' ')[1])
                result['video_fps'] = tbr

            except:
                match = re.search("( [0-9]*.| )[0-9]* fps", line)
                result['video_fps'] = float(line[match.start():match.end()].split(' ')[1])


            # It is known that a fps of 24 is often written as 24000/1001
            # but then ffmpeg nicely rounds it to 23.98, which we hate.
            coef = 1000.0/1001.0
            fps = result['video_fps']
            for x in [23,24,25,30,50]:
                if (fps!=x) and abs(fps - x*coef) < .01:
                    result['video_fps'] = x*coef

            if check_duration:
                result['video_nframes'] = int(result['duration']*result['video_fps'])+1
                result['video_duration'] = result['duration']
            else:
                result['video_nframes'] = 1
                result['video_duration'] = None
            # We could have also recomputed the duration from the number
            # of frames, as follows:
            # >>> result['video_duration'] = result['video_nframes'] / result['video_fps']


        lines_audio = [l for l in lines if ' Audio: ' in l]

        result['audio_found'] = lines_audio != []

        if result['audio_found']:
            line = lines_audio[0]
            try:
                match = re.search(" [0-9]* Hz", line)
                result['audio_fps'] = int(line[match.start()+1:match.end()-3])
            except:
                result['audio_fps'] = 'unknown'

        return result


def main():
    # parse command line options
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--mp4file1','-m1',default=None)
    parser.add_argument('--mp4file2','-m2',default=None)
    args = parser.parse_args()

    if args.mp4file1 and args.mp4file2:
        clip1 = mursClip(args.mp4file1)
        clip2 = mursClip(args.mp4file2)



if __name__ == "__main__":
    main()


