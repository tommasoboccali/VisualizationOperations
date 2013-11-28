// c++ xraise.cpp -L/usr/X11R6/lib -lX11 -o xraise
//
// Note for KDE users, which use Kwin.
//     You man need to disable the focus stilling option.
//     "Turn it off globally in Alt+F3/Configure/Advanced"
//     or in ~/.kde/share/config/kwinrc
//     FocusStealingPreventionLevel=0
//

#include <stdio.h>
#include <stdlib.h>
#include <X11/Xlib.h>

int main(int argc, char **argv){
  if ( argc != 2 ){
    printf("Usage:\n\txraise <window id>\n");
    return 1;
  }
  Display* dsp = XOpenDisplay(NULL);
  long id = strtol(argv[1], NULL, 16);
  /*
  XEvent event;
  XQueryPointer(dsp,RootWindow(dsp,DefaultScreen(dsp)),
		&event.xbutton.root, &event.xbutton.window,
		&event.xbutton.x_root, &event.xbutton.y_root,
		&event.xbutton.x, &event.xbutton.y,
		&event.xbutton.state);
  printf("Mouse Coordinates: %d %d\n", event.xbutton.x, event.xbutton.y);
  */
  XRaiseWindow(dsp,id);
  XSetInputFocus(dsp,id, RevertToNone, CurrentTime);

  XCloseDisplay(dsp);
  return 0;
}

