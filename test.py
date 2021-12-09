import sys, os

try:
    raise NotImplementedError("No error")
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(f"{e}\n\n{exc_type}\n\n{fname}\n\n{exc_tb.tb_lineno}")