// c++ xidle.cpp -L/usr/X11R6/lib -lX11 -lXss -o xidle
#include <stdio.h>
#include <X11/Xlib.h>
#include <X11/extensions/scrnsaver.h>
main(){
  XScreenSaverInfo *info = XScreenSaverAllocInfo();
  Display* display = XOpenDisplay(0);
  XScreenSaverQueryInfo(display, DefaultRootWindow(display), info);
  printf("%u ms\n",info->idle);
}
