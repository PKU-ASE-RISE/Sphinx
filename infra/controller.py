# -*- coding: utf-8 -*-
"""
安卓手机操控
"""
from pathlib import Path
from .context import Activity
from .hierarchy import Event, ActionType, UIHierarchy
from .util import Timer, center
import logging
from typing import Tuple, Union, cast
import uiautomator2 as u2
import os, time, random, subprocess, json
import xml.etree.ElementTree as ET
import string
import requests
globals().update(ActionType.__members__) # allow for shorter use of action types
def rand_pos(bound: Tuple[int, int, int, int], zoom: float) -> Tuple[int, int]:
    assert zoom > 0 and zoom <= 1, zoom
    (left, top, right, bottom) = bound
    (center_x,center_y) = ((left+right)/2,(top+bottom)/2)
    left = int(center_x - (center_x-left)*zoom)
    right = int(center_x + (right-center_x)*zoom)
    top = int(center_y - (center_y-top)*zoom)
    bottom = int(center_y + (bottom-center_y)*zoom)
    right = max(left+1,right)
    bottom = max(top+1,bottom)
    return (random.randint(left, right), random.randint(top, bottom))

def sanitize(x: float, y: float) -> Tuple[float, float]:
    return max(x,5), max(y,5)

STR_MIN_LEN, STR_MAX_LEN = 5, 10
DRAG_MIN_STEP, DRAG_MAX_STEP = 1, 10
character_list = ['\$','\%','\&','\*','\.','\/','\<','\>','\?','\@','\_'] # type: ignore

def ParseBound(bounds: str) -> Tuple[int, int, int, int]:
    left_top,right_bot = bounds.split('][')
    x1,y1 = left_top[1:].split(',')
    x2,y2 = right_bot[:-1].split(',')
    y1,y2 = int(y1),int(y2)
    x1,x2 = int(x1),int(x2)
    return (x1,y1,x2,y2)

# BUG: the documentation is out-dated
def find_bottom(root, default):
    """Perform a Depth-First Search on an XML Element and return the first leaf node encountered."""

    resource_id = "com.android.systemui:id/recent_apps"
    if 'resource-id' in root.attrib and root.attrib['resource-id'] == resource_id:
        return ParseBound(root.attrib['bounds'])[1]
    ret = default
    for node in root:
        ret = find_bottom(node,default)
        if ret != default:
            return ret
    return default
        

class AndroidController:
    """Controller class for performing actions and retrieving response on AUT.
    安卓手机控制
    
    Attributes:
        port: ID of device running AUT
        device: uiautomator2 object representing the device
        device_info: info of device running AUT
        magic_bound: device screenheight
        upperbar: height of upper bar in AUT that needs to be skipped in coordinate calculation
        subbar: bottom version of upperbar, not being used
        sleep_time: not sure? Not used in any class methods
        app_pkg_name: apk name of AUT (e.g. "com.google.launcher")
        magic_offset: Not sure, seems to return the first leaf node in the UI hierarchy? TODO
        default_ime: TODO
        fast_ime: TODO
        null_ime: TODO
    """
    port: str; app_pkg_name: str
    device_url: str
    device_info: dict
    upperbar: int; subbar: int; sleep_time: float
    default_ime: str; fast_ime: str; null_ime: str
    magic_offset: int
    popup_name: str

    def __init__(self, port: str, target_app):
        device = u2.connect_usb(port)
        if not device:
            logging.error('init Android opr failed!')
        else:
            logging.info('init Android opr success!')

        self.port = port
        self.device = device
        # self.device_url = self.device._get_atx_agent_url()
        self.device_info = cast(dict, self.device.device_info)
        # self.magic_bound = self.device.info['displayHeight']
        self.upperbar = 0
        self.subbar = 0
        self.sleep_time = 0.1
        self.app_pkg_name = target_app
        # self.magic_offset = find_bottom(ET.fromstring(self.device.dump_hierarchy()), self.device_info['display']['height']) - 20 - self.magic_bound
        self.default_ime = "com.baidu.input_hihonor/com.baidu.input_honor.ImeService"
        self.fast_ime = "com.github.uiautomator/.FastInputIME"
        self.null_ime = "com.wparam.nullkeyboard/.NullKeyboard"

        # os.environ['BOTTOM_LOWER_BOUND'] = str(self.magic_bound+self.magic_offset)
        self.popup_name = 'PopupWindow'

    def disable_soft_keyboard(self, null_ime_path: str):
        shell_reponse = self.device.shell('ime list -s | grep {}'.format(self.null_ime))
        null_ime_exist = shell_reponse.output.strip()
        err_code = shell_reponse.exit_code
        time.sleep(2)
        if err_code != 0 or null_ime_exist != self.null_ime:
            if not os.path.exists(null_ime_path):
                logging.critical('path of nullkeyboard.apk not set, using default ime...')
                return 
            logging.error('installing null keyboard')
            os.popen(f'adb -s {self.port} install nullkeyboard.apk')
            time.sleep(5)
            with self.device.watch_context() as ctx:
                ctx.when("继续").click()
                time.sleep(3)
                ctx.when("继续安装").click()
                time.sleep(3)
                ctx.when("完成").click()
                time.sleep(3)
            logging.error('null keyboard installed')
        else:
            logging.error('null keyboard already installed')
        logging.error(f'activating null keyboard ime on device {self.port}')
        
        self.device.shell('ime enable {}'.format(self.null_ime))
        time.sleep(3)
        self.device.shell(f"ime set {self.null_ime}")
        time.sleep(3)
        with self.device.watch_context() as ctx:
            ctx.when("继续").click()
        time.sleep(3)
        logging.error(f'null keyboard ime is activated on device {self.port}')

    def monitor_popups(self):
        """Periodically check for system popups."""
        self.device.watch_context(autostart=True,builtin=True)

    def start_app(self, app_pkg_name: Union[str, None] = None, wait: int=2):
        """Launch apk with the given name on device.
        启动app
        :param app_pkg_name:
        :return:
        """
        self.device.app_start(self.app_pkg_name if app_pkg_name is None else app_pkg_name, use_monkey=True)
        logging.debug('start app begin...')
        time.sleep(wait)
        logging.debug('start app end...')

    def uninstall_app(self, app_pkg_name: str):
        """Uninstall apk with the given name on device.
        卸载app
        :param app_pkg_name:
        :return:
        """
        self.device.app_uninstall(app_pkg_name)
    
    def install_app(self, app_pkg_name: str, app_path: Path):
        """Install apk with the given name on device.
        安装app
        :param app_pkg_name:
        :return:
        """
        self.device.app_install(app_path)

    def reinstall_app(self, app_pkg_name: str, app_path: Path):
        """Reinstall apk with the given name on device.
        重装app
        :param app_pkg_name:
        :return:
        """
        self.uninstall_app(app_pkg_name)
        print(app_path)
        self.install_app(app_pkg_name, app_path)
        self.start_app(app_pkg_name)

    def stop_app(self, app_pkg_name: str = None):
        """Halt control of device.
        app杀进程
        :param app_pkg_name:
        :return:
        """
        app_pkg_name = self.app_pkg_name if app_pkg_name is None else app_pkg_name
        if app_pkg_name == 'com.android.launcher3':
            logging.critical('tried to kill launcher3!')
        else:
            self.device.app_stop(app_pkg_name)

    def click(self, x: float, y: float, wait_time: float = 0.0):
        """Tap the device screen at position (x,y)."""
        self.device.shell(f'input tap {int(x)} {int(y) + self.upperbar}')
        time.sleep(wait_time)

    def doubleclick(self, x: int, y: int, wait_time: float = 0.0):
        self.device.double_click(int(x), int(y) + self.upperbar)
        time.sleep(wait_time)

    def home(self):
        """Activate device home button."""
        self.device.press("home")

    def back(self):
        """Go back on device."""
        self.device.shell('input keyevent KEYCODE_BACK')

    def enter(self):
        """Activate device enter button."""
        self.device.press("enter")

    def tap_hold(self, x: float, y: float, t: float):
        """Tap and hold the screen at position (x,y) for t seconds."""
        self.device.shell(f'input swipe {int(x)} {int(y) + self.upperbar} {int(x)} {int(y) + self.upperbar} {int(t*1000)}')

    def horizontal_scroll(self, start: int = 200, end: int = 800, pos: int = 500, direction: int = 1):
        if direction==1:
            self.swipe(start, pos, end, pos)
        else:
            self.swipe(end, pos, start, pos)

    def swipe(self, fx: float, fy: float, tx: float, ty: float, wait_time: float = 0.0):
        self.device.shell(f"input swipe {int(fx)} {int(fy)} {int(tx)} {int(ty)} 100")
        time.sleep(wait_time)

    def input(self, text: str = "PKU", clear: bool = True, wait_time: float = 0.0):
        try:
            self.device.shell(f"ime set {self.fast_ime}")
            self.device.send_keys(text,clear = clear)
            self.device.shell(f"ime set {self.null_ime}")
            time.sleep(wait_time)
            return True
        except:
            return False

    def capture_screen(self, format = "opencv"):
        """Take a screenshot of the device screen.
        截屏
        :return:
        """
        return self.device.screenshot(format=format)

    def dumpstr(self) -> str:
        return self.device.dump_hierarchy()
    
    def dump(self) -> UIHierarchy:
        """Return a XML ElementTree from AUT."""
        return UIHierarchy(ET.fromstring(self.device.dump_hierarchy()))

    def fast_dump(self) -> Union[str, None]:
        raise NotImplementedError("This method is discarded since uiautomator2 3.x version. If you need to use it, check how to get device_url in the new version.")
        url = self.device_url + '/dump/hierarchy'
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    
    def wrapper_app_current(self) -> dict:
        try:
            CurApp = self.device.app_current()
        except OSError:
            logging.critical('uiautomator app_current failed!')
            subprocess.Popen('adb shell monkey -p com.android.launcher3 1',shell=True).wait()
            CurApp = self.device.app_current()
        except:
            raise 
        return CurApp

    def activity(self, slow: bool = False) -> Activity:
        """Return the package name of the app currently open on the device as well as the specific activity it's on."""
        if slow:
            cur_app = self.device.app_current()
            return Activity(cur_app['package'], cur_app['activity'])
        
        try:
            response = self.device.shell('dumpsys window | grep mCurrentFocus').output.strip().split(' ')[-1]
            pkg_name, activity = response.split('/')
            activity = activity.strip('}')
        except:
            # PopUpWindow
            cur_app = self.device.app_current()
            pkg_name, activity = cur_app['package'], cur_app['activity']
            activity = self.popup_name
        return Activity(pkg_name, activity)

    def clear_user_data(self):
        self.device.shell('pm clear {}'.format(self.app_pkg_name))

    def restore_app(self):
        """TODO documentation"""
        self.device.press('recent')
        time.sleep(0.2)
        self.device.press('back')
        time.sleep(0.1)
        self.device.press('recent')
        self.device.press('recent')

    def grant_permission(self, permissions):
        """TODO documentation"""
        for permission in permissions:
            logging.debug('grant permission {}'.format(permission))
            self.device.shell('pm grant {} {}'.format(self.app_pkg_name,permission))

    def revoke_permission(self, permissions):
        """TODO documentation"""
        for permission in permissions:
            logging.debug('revoke permission {}'.format(permission))
            self.device.shell('pm revoke {} {}'.format(self.app_pkg_name, permission))
            
    def correct_pos(self, root:ET.Element) -> ET.Element:
        """TODO documentation"""
        raise NotImplementedError("This method is discarded since uiautomator2 3.x version. If you need to use it, check how to get magic_bound and magic_offset in the new version.")
        for node in root.iter():
            if 'bounds' in node.attrib:
                bounds = node.attrib['bounds']
                bounds = bounds[1:-1].split('][')
                bounds = [int(x) for x in bounds[0].split(',')+bounds[1].split(',')]
                if bounds[3] == self.magic_bound:
                    bounds[3] += self.magic_offset
                    node.attrib['bounds'] =  f"[{bounds[0]},{bounds[1]}][{bounds[2]},{bounds[3]}]"
        return root
    
    def wifi_switch(self, switch: bool):
        """TODO documentation"""
        if switch:
            self.device.shell('svc wifi enable')
        else:
            self.device.shell('svc wifi disable')
            
    def air_mode_switch(self, switch: bool):
        """TODO documentation"""
        if switch:
            self.device.shell('settings put global airplane_mode_on 1')
            self.device.shell('am broadcast -a android.intent.action.AIRPLANE_MODE')
        else:
            self.device.shell('settings put global airplane_mode_on 0')
            self.device.shell('am broadcast -a android.intent.action.AIRPLANE_MODE')
    
    def screen_wake(self, switch: bool):
        """Wake the screen and swipe to unlock the device.
        
        Doesn't work if device is locked
        """
        if switch:
            self.device.screen_on()
            time.sleep(0.1)
            self.device.swipe(540, 2000, 540, 200, 0.2)
            
        else:
            self.device.screen_off()
            time.sleep(0.2)
            
    def screen_rotate(self):
        """TODO documentation"""
        self.device.set_orientation('l')
        self.device.set_orientation('r')
        self.device.set_orientation('n')
            
    def recover_uiautomator(self):
        raise NotImplementedError()
        
def activity_monitor(controller: AndroidController):
    """Monitor changes in app and compare results

    This function runs in the background somehow and checks what activities the AUT has gone through since this was called.
    On KeyboardInterrupt, this function checks for previous monitor logs and compares their activities explored with 
    the current run, printing out the final info and creating a new updated log. 
    Returns every activity explored both in this run and all previous runs. 

    :return all_activities:
    """
    last_app,last_activity = None,None
    all_activities = set()
    try:
        while True:
            app, activity = controller.activity().info()
            if app != last_app or activity != last_activity:
                print(app,activity)
                last_app,last_activity = app,activity
            if app == controller.app_pkg_name:
                all_activities.add(activity)
    except KeyboardInterrupt:
        print(all_activities)
        new_covered_activities = set()
        if os.path.exists(f'test/manual_{controller.app_pkg_name}_activity.json'):
            with open(f'test/manual_{controller.app_pkg_name}_activity.json','r') as f:
                old_activities = json.load(f)
            new_covered_activities = all_activities.difference(set(old_activities))
            all_activities = all_activities.union(set(old_activities))
        with open(f'test/manual_{controller.app_pkg_name}_activity.json','w') as f:
            json.dump(list(all_activities),f,indent=4)
        print(len(all_activities))
        print(new_covered_activities)
        print(len(new_covered_activities))
        return all_activities
        

if __name__ == "__main__":
    app = 'douzifly.list'
    controller = AndroidController('emulator-5554',app)
    with Timer("app info time"):
        print(controller.activity().info())
    with Timer("dump time"):
        controller.dump()
    with open('h.xml', 'w') as out:
        out.write(controller.dumpstr())
    with Timer("screenshot time"):
        controller.capture_screen().dump("screen.png")
