from distutils.core import setup
import py2exe

setup(console=['Client.py'], options={
    'py2exe': {
        'packages': ['os',
                     'socket',
                     'time',
                     'random',
                     'cv2',
                     'GetIP',
                     'Crypto',
                     'webbrowser',
                     'subprocess',
                     'pyaudio'],
        'dll_excludes': ["MSVFW32.dll",
                         "AVIFIL32.dll",
                         "AVICAP32.dll",
                         "ADVAPI32.dll",
                         "CRYPT32.dll",
                         "WLDAP32.dll"]
    }

})
