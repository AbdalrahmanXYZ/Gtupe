# window.py
#
# Copyright 2022 Abdalrahman Azab
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import GObject, Gtk, Adw, Pango, Gdk
import pytube
import re
import sqlite3
import threading
import time
import datetime
import html
import urllib


@Gtk.Template(resource_path='/com/github/azab/gtupe/window.ui')
class GtupeWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'GtupeWindow'

    MainBuffer = Gtk.Template.Child()
    MainEntry = Gtk.Template.Child()
    MainRevealer = Gtk.Template.Child()
    ListSuggestionRevealer = Gtk.Template.Child()
    SubmitButton = Gtk.Template.Child()
    List_revealer = Gtk.Template.Child()
    loading_revealer = Gtk.Template.Child()
    vid_revealer = Gtk.Template.Child()
    done_revealer = Gtk.Template.Child()
    fail_revealer = Gtk.Template.Child()
    Playlist_Content_Group = Gtk.Template.Child()
    Carousel = Gtk.Template.Child()
    LoadingAdwPage = Gtk.Template.Child()
    ListNameLabel = Gtk.Template.Child()
    VidDetails = Gtk.Template.Child()
    VidTypeBox = Gtk.Template.Child()
    VidResBox = Gtk.Template.Child()
    VidResLabel = Gtk.Template.Child()
    ListTypeBox = Gtk.Template.Child()
    ListResBox = Gtk.Template.Child()
    ListResLabel = Gtk.Template.Child()
    VidSizeLabel = Gtk.Template.Child()
    SuggestionCheck = Gtk.Template.Child()
    Error_Label = Gtk.Template.Child()
    LoadingProgressBar = Gtk.Template.Child()
    VidRequest = 0
    ListRequest = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.MainBuffer.connect("inserted_text", self.islistq)
        self.MainBuffer.connect("deleted_text", self.islistq)



    def time_format(self, sec):
        if sec >= 60 and sec < 3600:
            result = f"{float(sec / 60):.2f}" + " min"
        elif sec >= 3600:
            result = f"{float(sec / 60 / 60):.2f}" + " hrs"
        else:
            result = f"{int(sec)}" + " sec"
        return result

    def size_format(self, size):
            tags = ["bytes", "Kb", "Mb", "Gb", "Tb"]
            i = 0
            double_bytes = size
            while (i < len(tags) and  size >= 1024):
                    double_bytes = size / 1024.0
                    i = i + 1
                    size = size / 1024
            return str(round(double_bytes, 2)) + " " + tags[i]


    def AddToTasksDB(self, url, res, dtype, loc, size):
        fsize = self.size_format(size)
        dt = datetime.now().strftime("%d/%m/%Y %H:%M")
        conn = sqlite3.connect('tm')
        self.db = conn.cursor()
        self.db.execute('''
          CREATE TABLE IF NOT EXISTS Downloads
          ([url] TEXT, [res] TEXT, [type] TEXT, [location] TEXT, [added_on] TEXT, [size] TEXT)
          ''')
        self.db.execute('''INSERT INTO Downloads (url, res, type, location, added_on, size) VALUES (?, ?, ?, ?, ?)''', url, res, dtype, loc, dt, fsize)


    #def Download_handler(self, Pause_p, Resume_p, Cancel_p, PBar, Url, Res, Type, Loc):



    def UpdateDownloads():
        waiting = self.db.execute("SELECT * FROM Downloads")
        i = 0
        for row in waiting:
            if row not in self.downloading:
                self.downloading.append(row)
                self.downloading[i]["url"]
                self.downloading[i]["res"]
                self.downloading[i]["type"]
                self.downloading[i]["location"]
                self.downloading[i]["added_on"]
                self.downloading[i]["size"]

                i += 1

    #def UpdateHistory():

    def Video_Data(self, *args):
        if self.connect_func() == False:
                return
        try:
            self.VidRequest = 1
            self.VidVidRes = Gtk.ListStore(str)
            self.VidAuidRes = Gtk.ListStore(str)
            self.VidTypeList = Gtk.ListStore(str)
            # setting lables
            self.link = self.MainBuffer.get_text()
            self.vid = pytube.YouTube(self.link)
            self.VidDetails.set_title(html.escape(self.vid.title))
            self.VidDetails.set_description(f"Channel: {html.escape(self.vid.author)}  Length: " + f"{self.time_format(self.vid.length)}" + "   Views: " + f"{self.vid.views:,}")
            # setting combo boxes data
            self.SizesA = []
            self.SizesV = []
            for stream in self.vid.streams.filter(progressive = True):
                self.VidVidRes.append([f'{stream.resolution}'])
                self.SizesV.append(self.size_format(stream.filesize))
                print(stream.resolution)
            for stream in self.vid.streams.filter(only_audio = True):
                self.VidAuidRes.append([f'{round(stream.bitrate/1000)}kbps'])
                self.SizesA.append(self.size_format(stream.filesize))
                print(stream.bitrate)
            self.VidTypeList.append(['Video'])
            self.VidTypeList.append(['Audio'])
            print('70%')
            # cell R
            # type
            self.VidTypeBox.set_model(self.VidTypeList)
            renderer_text = Gtk.CellRendererText.new()
            self.VidTypeBox.pack_start(renderer_text, True)
            self.VidTypeBox.add_attribute(renderer_text, "text", 0)
            self.VidTypeBox.set_active(0)
            # res
            self.VidResBox.set_model(self.VidVidRes)
            renderer_textv = Gtk.CellRendererText.new()
            self.VidResBox.pack_start(renderer_textv, True)
            self.VidResBox.add_attribute(renderer_textv, "text", 0)
            self.VidResBox.set_active(0)
            self.size_label_handler()
            print('100%')
            # finishing loading process
            self.loading = 0
            self.loading_revealer.set_reveal_child(False)
            self.vid_revealer.set_reveal_child(True)
            self.Carousel.scroll_to(self.vid_revealer, True)
            return
        except Exception as err:
            if err:
                self.loading = 0
                self.Fail(err)
                return

    def Playlist_Data(self, *args):
        global rows
        global check
        if self.connect_func() == False:
                return
        try:
            self.ListRequest = 1
            #func
            self.ListVidRes = Gtk.ListStore(str)
            self.ListAuidRes = Gtk.ListStore(str)
            self.ListTypeList = Gtk.ListStore(str)
            self.link = self.MainBuffer.get_text()
            i = 0
            self.plist = pytube.Playlist(self.link)
            self.l = len(self.plist.videos)
            rows = [0]*self.l
            check = [0]*self.l
            print("rows done")
            for video in self.plist.videos:
                # card box
                rows[i] = Adw.ActionRow.new()
                check[i] = Gtk.CheckButton.new()
                check[i].set_active(True)
                check[i].add_css_class("selection-mode")
                rows[i].add_prefix(check[i])
                # desc
                rows[i].set_title(html.escape(video.title))
                rows[i].set_subtitle(f"Channel: {html.escape(video.author)} Length: " + f"{self.time_format(video.length)}" + " Views: " + f"{video.views:,}")
                self.Playlist_Content_Group.add(rows[i])
                i += 1
                print(i)
            self.ListNameLabel.set_label(self.plist.title)
            # setting combo boxes data
            for stream in self.plist.videos[0].streams.filter(progressive = True):
                self.ListVidRes.append([f'{stream.resolution}'])
                print(stream.resolution)
            for stream in self.plist.videos[0].streams.filter(only_audio = True):
                self.ListAuidRes.append([f'{round(stream.bitrate/1000)}kbps'])
                print(stream.bitrate)
            self.ListTypeList.append(['Video'])
            self.ListTypeList.append(['Audio'])
            # cell R
            # type
            self.ListTypeBox.set_model(self.ListTypeList)
            renderer_text = Gtk.CellRendererText.new()
            self.ListTypeBox.pack_start(renderer_text, True)
            self.ListTypeBox.add_attribute(renderer_text, "text", 0)
            self.ListTypeBox.set_active(0)
            # res
            self.ListResBox.set_model(self.ListVidRes)
            renderer_textv = Gtk.CellRendererText.new()
            self.ListResBox.pack_start(renderer_textv, True)
            self.ListResBox.add_attribute(renderer_textv, "text", 0)
            self.ListResBox.set_active(0)
            # finishing loading process
            self.loading = 0
            self.loading_revealer.set_reveal_child(False)
            self.List_revealer.set_reveal_child(True)
            self.Carousel.scroll_to(self.List_revealer, True)
            print("022f")
            return
        except Exception as err:
            if err:
                self.loading = 0
                self.Fail(err)
                return


    def loading_func(self):
        while self.loading == 1:
            self.LoadingProgressBar.pulse()
            time.sleep(0.25)

    def connect_func(self):
        try:
            host='http://google.com'
            urllib.request.urlopen(host)
            print("One Connection Has Been Established")
            return True
        except:
            print("Connection Failed")
            self.Fail("Failed Due To Connection Cut")
            return False

    def islistq(self, *args):
        # if a vid related to a list
        if re.findall(".*youtube\.com/watch\?v\=.{11}&list\=.{34}.*", self.MainBuffer.get_text()) or re.findall(".*youtu\.be/.{11}\?list\=.{34}.*", self.MainBuffer.get_text()):
            self.SubmitButton.set_label("Download Video")
            self.ListSuggestionRevealer.set_reveal_child(True)
            self.SubmitButton.set_sensitive(True)
            print("a vid related to a list")
            return 0
        # if a playlist
        elif re.findall(".*youtube\.com/playlist\?list\=.{34}.*", self.MainBuffer.get_text()):
            self.SubmitButton.set_label("Download Playlist")
            self.ListSuggestionRevealer.set_reveal_child(False)
            self.SubmitButton.set_sensitive(True)
            print("playlist")
            return 1
        # if a plain vid
        elif re.findall(".*youtube\.com/watch\?v\=.{11}.*", self.MainBuffer.get_text()) or re.findall(".*youtu\.be\/.{11}.*", self.MainBuffer.get_text()) and not (re.findall(".*youtube\.com/watch\?v\=.{11}&list\=.{34}.*", self.MainBuffer.get_text()) or re.findall(".*youtu.be/.{11}\?list\=.{34}.*", self.MainBuffer.get_text())):
            self.ListSuggestionRevealer.set_reveal_child(False)
            self.SubmitButton.set_sensitive(True)
            self.SubmitButton.set_label("Download Video")
            print("plain vid")
            return 2
        else:
            self.ListSuggestionRevealer.set_reveal_child(False)
            self.SubmitButton.set_sensitive(False)
            print("invalid url")
            return 3


    @Gtk.Template.Callback()
    def Submit_Func(self, button):
        if self.islistq() == 1:
            self.MainRevealer.set_reveal_child(False)
            self.loading_revealer.set_reveal_child(True)
            self.Carousel.scroll_to(self.loading_revealer, True)
            self.loading = 1
            threading.Thread(target = self.loading_func, daemon = True).start()
            threading.Thread(target = self.Playlist_Data, daemon = True).start()
            print("022")
        elif self.islistq() == 2:
            self.MainRevealer.set_reveal_child(False)
            self.loading_revealer.set_reveal_child(True)
            self.Carousel.scroll_to(self.loading_revealer, True)
            self.loading = 1
            threading.Thread(target = self.loading_func, daemon=True).start()
            threading.Thread(target = self.Video_Data, daemon=True).start()
            print("023")

    @Gtk.Template.Callback()
    def on_vid_type_change(self, combo):
        if self.VidTypeBox.get_active() == 0:
            self.VidResBox.set_model(self.VidVidRes)
            self.VidResLabel.set_label("Resouloution :")
            self.VidResBox.set_active(0)
        else:
            self.VidResBox.set_model(self.VidAuidRes)
            self.VidResLabel.set_label("Bitrate :")
            self.VidResBox.set_active(0)


    @Gtk.Template.Callback()
    def on_list_type_change(self, combo):
        if self.ListTypeBox.get_active() == 0:
            self.ListResBox.set_model(self.ListVidRes)
            self.ListResLabel.set_label("Resouloution :")
            self.ListResBox.set_active(0)
        else:
            self.ListResBox.set_model(self.ListAuidRes)
            self.ListResLabel.set_label("Bitrate :")
            self.ListResBox.set_active(0)


    @Gtk.Template.Callback()
    def size_label_handler(self, *args):
        if self.VidTypeBox.get_active() == 0:
            self.VidSizeLabel.set_label(f" Size : {self.SizesV[self.VidResBox.get_active()]}")
        else:
            self.VidSizeLabel.set_label(f" Size : {self.SizesA[self.VidResBox.get_active()]}")

    @Gtk.Template.Callback()
    def On_Go_Back(self, button):

        if self.VidRequest == 1:
            self.VidVidRes.clear()
            self.VidAuidRes.clear()
            self.VidTypeList.clear()
            self.VidResBox.clear()
            self.VidTypeBox.clear()
            self.VidRequest = 0

        if self.ListRequest == 1:
            self.ListVidRes.clear()
            self.ListAuidRes.clear()
            self.ListTypeList.clear()
            self.ListResBox.clear()
            self.ListTypeBox.clear()
            for i in range(len(rows)):
                try:
                    rows[i].remove(check[i])
                    check[i].run_dispose()
                except Exception as e:
                    print(str(e))
                    pass
                try:
                    self.Playlist_Content_Group.remove(rows[i])
                    rows[i].run_dispose()
                except Exception as e:
                    print(str(e))
                    pass
            self.ListRequest = 0

        self.VidSizeLabel.set_label("")
        self.MainEntry.set_text("")
        loading = 0
        self.MainRevealer.set_reveal_child(True)
        self.SubmitButton.set_sensitive(False)
        self.SuggestionCheck.set_active(False)
        self.ListSuggestionRevealer.set_reveal_child(False)
        self.Carousel.scroll_to(self.MainRevealer, True)
        self.List_revealer.set_reveal_child(False)
        self.vid_revealer.set_reveal_child(False)
        self.done_revealer.set_reveal_child(False)
        self.fail_revealer.set_reveal_child(False)


    def Fail(self, errno):
        if 'Errno -3' in str(errno):
            self.Error_Label.set_label("Error: Conection Error")
        else:
            self.Error_Label.set_label("Error: "+ str(errno))
        self.MainRevealer.set_reveal_child(False)
        self.SubmitButton.set_sensitive(False)
        self.SuggestionCheck.set_active(False)
        self.List_revealer.set_reveal_child(False)
        self.vid_revealer.set_reveal_child(False)
        self.done_revealer.set_reveal_child(False)
        self.fail_revealer.set_reveal_child(True)
        self.Carousel.scroll_to(self.fail_revealer, True)


class AboutDialog(Gtk.AboutDialog):

    def __init__(self, parent):
        Gtk.AboutDialog.__init__(self)
        self.props.program_name = 'Gtupe'
        self.props.version = "0.1.0"
        self.props.authors = ['Abdalrahman Azab']
        self.props.copyright = '2022 Abdalrahman Azab'
        self.props.logo_icon_name = 'com.github.azab.gtupe'
        self.props.modal = True
        self.set_transient_for(parent)

