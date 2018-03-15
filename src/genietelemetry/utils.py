


ESCAPE_STD = (("&", "&amp;"),
              ("<", "&lt;"),
              (">", "&gt;"),
              ("\"", "&quot;"),
              ("\n", "\u000A"))

def escape(stdinput):

    for esc in ESCAPE_STD:
        stdinput = stdinput.replace(*esc)

    return stdinput