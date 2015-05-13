from os import path, sys, pardir

try:
	APP_ROOT = path.dirname(path.abspath(__file__))
except NameError:  # We are the main py2exe script, not a module
	APP_ROOT = path.dirname(path.abspath(sys.argv[0]))

APP_ROOT = path.abspath(path.join(APP_ROOT, pardir))

APP_CONFIG_FILE = APP_ROOT + "/winch-pc.ini" 

APP_DEFAULTS = {
	"mac-address" 	: "00:06:66:43:11:8D",
	"com-port"		: "16"
}
