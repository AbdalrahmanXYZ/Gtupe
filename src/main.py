# main.py
#
# Copyright 2022 Abdalrahman Azab
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import GObject, Gtk, Adw, Pango, Gdk, Gio, GLib
import pytube
import re
import sqlite3
import threading
import time
import datetime as d
import html
import urllib
import os



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
    Downloads = {"URL" : [], "Row" : [], "MainBox" : [], "MainIcon" : [],
                 "InnerBox1" : [], "InnerBox2" : [], "InnerBox3" : [],
                 "Title" : [], "Subtitle" : [], "ButtonBox" : [], "Stop" : [],
                 "Pause" : [], "ProgressBar" : [], "IsPaused" : [], "isCanceled" : []}
    VidRequest = 0
    ListRequest = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        global DefaultLocFileDir
        global DefaultLocPATH
        self.MainBuffer.connect("inserted_text", self.islistq)
        self.MainBuffer.connect("deleted_text", self.islistq)
        DefaultLocFileDir = GLib.get_user_cache_dir() + "/tmp/DefaultDownloadLoc"
        try:
            with open(DefaultLocFileDir, 'r') as f:
                DefaultLocPATH = f.read()
                print(DefaultLocPATH)
            f.close
        except FileNotFoundError:
            with open(DefaultLocFileDir, 'x') as f:
                f.close()
            with open(DefaultLocFileDir, 'w') as f:
                f.write(GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD))
                DefaultLocPATH = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
                f.close()



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

    def AddToTasksDB(self, url, res, dtype, size, name):
        self.cache_dir = GLib.get_user_cache_dir()
        fsize = self.size_format(size)
        dt = d.datetime.now().strftime("%d/%m/%Y %H:%M")
        conn = sqlite3.connect(self.cache_dir + '/tmp/GtupeData.db')
        self.db = conn.cursor()
        self.db.execute('''
          CREATE TABLE IF NOT EXISTS Downloads
          ([url] TEXT, [res] TEXT, [type] TEXT, [location] TEXT, [added_on] TEXT, [size] TEXT, [name] TEXT)
          ''')
        print(res)
        self.db.execute("INSERT INTO Downloads (url, res, type, location, added_on, size, name) VALUES (?, ?, ?, ?, ?, ?, ?)", (url, str(res), dtype, GtupeApplication.Update_Download_Path(GtupeApplication), dt, fsize, name))
        conn.commit()
        conn.close()
        threading.Thread(target = self.UpdateDownloads, daemon = True).start()
    #def Download_handler(self, IsPaused, IsCanceled, PBar, Url, Res, Type, Loc):



    def UpdateDownloads(self, *args):
        conn = sqlite3.connect(self.cache_dir + '/tmp/GtupeData.db')
        self.db = conn.cursor()
        queue = self.db.execute("SELECT * FROM Downloads")
        #if len(queue) == 1:
            #return
        for video in queue:
            print(video)
            if video[0] not in self.Downloads["URL"]:
                # creating row widgets
                curr = len(self.Downloads["URL"])
                print(curr)
                # setting row and url value
                self.Downloads["URL"].append(video[0])
                self.Downloads["Row"].append(Adw.ActionRow.new())
                self.Downloads["IsPaused"].append(False)
                #self.Downloads["IsCanceled"].append(False)
                # setting MainBox Defaults
                self.Downloads["MainBox"].append(Gtk.Box)
                self.Downloads["MainBox"][curr].set_hexpand(True)
                self.Downloads["MainBox"][curr].set_margin_bottom(10)
                self.Downloads["MainBox"][curr].set_margin_start(10)
                self.Downloads["MainBox"][curr].set_margin_end(10)
                self.Downloads["MainBox"][curr].set_margin_top(10)
                # setting MainIcon Defaults
                if video[2] == "Video":
                    self.Downloads["MainIcon"].append(Gtk.Image.new_from_icon_name("video-x-generic-symbolic"))
                else:
                    self.Downloads["MainIcon"].append(Gtk.Image.new_from_icon_name("audio-x-generic-symbolic"))
                self.Downloads["MainIcon"][curr].set_margin_end(10)
                self.Downloads["MainIcon"][curr].set_pixel_size(50)
                # setting InnerBox1
                self.Downloads["InnerBox1"].append(Gtk.Box.new(orientation = "vertical", spacing = 10))
                self.Downloads["InnerBox1"][curr].set_hexpand(True)
                # setting InnerBox1
                self.Downloads["InnerBox2"].append(Gtk.Box)
                self.Downloads["InnerBox2"][curr].set_hexpand(True)
                # setting InnerBox1
                self.Downloads["InnerBox3"].append(Gtk.Box.new(orientation = "vertical", spacing = 0))
                self.Downloads["InnerBox3"][curr].set_hexpand(True)
                # setting Title
                self.Downloads["Title"].append(Gtk.Label.new(video[6]))
                self.Downloads["Title"][curr].set_ellipsize(3)
                self.Downloads["Title"][curr].set_max_width_chars(25)
                self.Downloads["Title"][curr].set_xalign(0)
                self.Downloads["Title"][curr].add_css_class("heading")
                # setting Subtitle
                self.Downloads["Subtitle"].append(Gtk.Label.new(video[4] + "  " + video[1] + "  " + video[5]))
                self.Downloads["Subtitle"][curr].set_ellipsize(3)
                self.Downloads["Subtitle"][curr].set_max_width_chars(25)
                self.Downloads["Subtitle"][curr].set_xalign(0)
                self.Downloads["Subtitle"][curr].set_sensitive(False)
                # setting Buttons
                self.Downloads["ButtonBox"].append(Gtk.Box.new(orientation = "vertical", spacing = 10))
                self.Downloads["Stop"].append(Gtk.Button.new_from_icon_name("media-playback-stop-symbolic"))
                self.Downloads["Stop"][curr].add_css_class("destructive-action")
                self.Downloads["Pause"].append(Gtk.Button.new_from_icon_name("media-playback-start-symbolic"))
                self.Downloads["Pause"][curr].add_css_class("accent")
                # setting ProgressBar
                self.Downloads["ProgressBar"].append(Gtk.ProgressBar.new())
                # structuring them
                self.Downloads["Row"][curr].set_child(self.Downloads["MainBox"][curr])
                self.Downloads["MainBox"][curr].append(self.Downloads["MainIcon"][curr])
                self.Downloads["MainBox"][curr].append(self.Downloads["InnerBox1"])
                self.Downloads["InnerBox1"][curr].append(self.Downloads["InnerBox2"])
                self.Downloads["InnerBox1"][curr].append(self.Downloads["ProgressBar"])
                self.Downloads["InnerBox2"][curr].append(self.Downloads["InnerBox3"])
                self.Downloads["InnerBox2"][curr].append(self.Downloads["ButtonBox"])
                self.Downloads["InnerBox3"][curr].append(self.Downloads["Title"])
                self.Downloads["InnerBox3"][curr].append(self.Downloads["Subtitle"])
        conn.close()


    #def UpdateHistory():

    def Video_Data(self, *args):
        global VidURL
        global VidName

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
            VidName = self.vid.title
            self.VidDetails.set_description(f"Channel: {html.escape(self.vid.author)}  Length: " + f"{self.time_format(self.vid.length)}" + "   Views: " + f"{self.vid.views:,}")
            # setting combo boxes data
            self.SizesA = []
            self.SizesV = []
            self.ResV = []
            self.ResA = []
            for stream in self.vid.streams.filter(progressive = True):
                self.VidVidRes.append([f'{stream.resolution}'])
                self.ResV.append([f'{stream.resolution}'])
                self.SizesV.append(stream.filesize)
                print(stream.resolution)
            for stream in self.vid.streams.filter(only_audio = True):
                self.VidAuidRes.append([f'{round(stream.bitrate/1000)}kbps'])
                self.ResA.append([f'{stream.bitrate}'])
                self.SizesA.append(stream.filesize)
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
            VidURL = self.link

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
                rows[i].set_title_lines(1)
                rows[i].set_subtitle_lines(1)
                check[i] = Gtk.CheckButton.new()
                check[i].set_active(True)
                check[i].add_css_class("selection-mode")
                rows[i].add_prefix(check[i])
                # desc
                name = html.escape(video.title)
                if len(name) > 80:
                    name = name[:80]+"..."
                rows[i].set_title(name)
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
            self.VidSizeLabel.set_label(f" Size : {self.size_format(self.SizesV[self.VidResBox.get_active()])}")
        else:
            self.VidSizeLabel.set_label(f" Size : {self.size_format(self.SizesA[self.VidResBox.get_active()])}")

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

    @Gtk.Template.Callback()
    def On_Vid_Download(self, button):
        threading.Thread(target = self.On_Vid_DownloadFunc(button), daemon = True).start()

    def On_Vid_DownloadFunc(self, button):
        global VidRes
        global VidType
        global VidSize
        print("???1")
        if self.VidTypeBox.get_active() == 0:
            VidRes = self.ResV[self.VidResBox.get_active()]
            VidType = "Video"
            VidSize = self.SizesV[self.VidResBox.get_active()]
        else:
            VidRes = self.ResA[self.VidResBox.get_active()]
            VidType = "Audio"
            VidSize = self.SizesA[self.VidResBox.get_active()]
        print("???2")
        self.AddToTasksDB(VidURL, VidRes, VidType, VidSize, VidName)
        print("???3")



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



class GtupeApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(application_id='com.github.azab.gtupe',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.create_action('quit', self.quit, ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('DefaultLocation', self.on_DefaultLoc_action)


    def do_activate(self):

        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = GtupeWindow(application=self)
        win.present()

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        about = AboutDialog(self.props.active_window)
        about.present()

    def on_DefaultLoc_action(self, widget, _):
        # Setting The Dialog
        self.DefaultLocation = Gtk.MessageDialog(parent = self.props.active_window, message_type = 4)
        self.DefaultLocation.props.text = 'Edit Default Download Path'
        self.DefaultLocation.props.secondary_text = "Enter A Default Folder Path To Be Used In The Future Downloads"
        # Setting Dialog Widgets
        self.DefaultLocEntry = Gtk.Entry()
        DefaultLocPATH = self.Update_Download_Path()
        if len(DefaultLocPATH) > 52:
            self.DefaultLocEntry.set_placeholder_text(DefaultLocPATH[:52]+"...")
        else:
            self.DefaultLocEntry.set_placeholder_text(DefaultLocPATH)
        self.DefaultLocButtonBox = Gtk.Box.new(0, 10)
        self.DefaultCancel = Gtk.Button.new_with_label("Cancel")
        self.DefaultCancel.connect("clicked", self.on_DefaultLoc_Cancel)
        self.DefaultCancel.add_css_class("destructive-action")
        self.DefaultSave = Gtk.Button.new_with_label("Save")
        self.DefaultSave.connect("clicked", self.on_DefaultLoc_Save)
        self.DefaultSave.add_css_class("suggested-action")
        self.DefaultLocButtonBox.append(self.DefaultCancel)
        self.DefaultLocButtonBox.append(self.DefaultSave)
        self.DefaultLocButtonBox.set_halign(3)
        self.DefaultLocation.props.message_area.set_margin_top(20)
        self.DefaultLocation.props.message_area.set_margin_bottom(20)
        self.DefaultLocation.props.message_area.set_spacing(20)
        self.DefaultLocation.props.message_area.append(self.DefaultLocEntry)
        self.DefaultLocation.props.message_area.append(self.DefaultLocButtonBox)
        self.DefaultLocation.props.modal = True
        self.DefaultLocation.set_transient_for(self.props.active_window)
        self.Invalid_Path_Label = Gtk.Label.new("Invalid Directory :/")
        self.Invalid_Path_Label.add_css_class("heading")
        self.Invalid_Path_Revealer = Gtk.Revealer()
        self.Invalid_Path_Revealer.set_transition_duration(150)
        self.Invalid_Path_Revealer.set_transition_type(5)
        self.Invalid_Path_Revealer.set_child(self.Invalid_Path_Label)
        self.DefaultLocation.props.message_area.append(self.Invalid_Path_Revealer)
        self.DefaultLocation.present()

    def on_DefaultLoc_Cancel(self, *args):
        self.DefaultLocation.close()

    def Update_Download_Path(self, *args):
        with open(DefaultLocFileDir, 'r') as f:
            DefaultLocPATH = f.read()
        print(DefaultLocPATH)
        f.close()
        return DefaultLocPATH

    def on_DefaultLoc_Save(self, *args):
        if os.path.isdir(self.DefaultLocEntry.get_text()):
            with open(DefaultLocFileDir, 'w') as f:
                f.write(self.DefaultLocEntry.get_text())
            DefaultLocPATH = self.DefaultLocEntry.get_text()
            self.DefaultLocation.close()
            print("Successfully Set To " + DefaultLocPATH)
        else:
            threading.Thread(target = self.When_Invalid_Path, daemon = True).start()

    def When_Invalid_Path(self, *args):
        if self.Invalid_Path_Revealer.get_reveal_child() == False:
            print("Invalid Directory")
            self.Invalid_Path_Revealer.set_reveal_child(True)
            time.sleep(2)
            self.Invalid_Path_Revealer.set_reveal_child(False)

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = GtupeApplication()
    return app.run(sys.argv)