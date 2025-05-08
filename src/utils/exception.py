import asyncio
import inspect        
import sys
import datetime
import json
import pprint

def print_code_chain(exc_traceback, exc_type=None, exc_value=None):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\033[1;31m{'='*60}\033[0m")
    print(f"\033[1;31m[异常时间]\033[0m {now}")
    if exc_type and exc_value:
        print(f"\033[1;31m[异常类型]\033[0m {exc_type.__name__}")
        print(f"\033[1;31m[异常信息]\033[0m {exc_value}")
    print(f"\033[1;31m[执行代码链]\033[0m")
    tb = exc_traceback
    step = 1
    while tb:
        frame = tb.tb_frame
        lineno = tb.tb_lineno
        filename = frame.f_code.co_filename
        func_name = frame.f_code.co_name
        print(f"\033[1;35m第{step}步\033[0m  \033[1;33m函数名：{func_name}\033[0m  \033[1;34m路径：{filename}:{lineno}\033[0m")
        try:
            lines, start_line = inspect.getsourcelines(frame.f_code)
            code_line = lines[lineno - start_line].strip()
            print(f"  \033[0;36m报错代码: {code_line}\033[0m")
            
            # 输出当前作用域的变量
            print("  \033[0;32m当前作用域变量:\033[0m")
            locals_dict = frame.f_locals
            # 过滤掉一些内置变量和特殊变量
            filtered_locals = {k: v for k, v in locals_dict.items() 
                             if not k.startswith('__') and not callable(v)}
            if filtered_locals:
                for var_name, var_value in filtered_locals.items():
                    try:
                        # 如果是字典或json，优先用json.dumps格式化输出
                        if isinstance(var_value, dict):
                            try:
                                value_str = json.dumps(var_value, ensure_ascii=False, indent=2)
                                if len(value_str) > 100:
                                    value_str = value_str[:97] + "..."
                            except Exception:
                                value_str = "[无法用json序列化]"
                        else:
                            value_str = pprint.pformat(var_value, compact=True, width=80)
                            if len(value_str) > 100:
                                value_str = value_str[:97] + "..."
                        print(f"    {var_name} = {value_str}")
                    except Exception:
                        print(f"    {var_name} = [无法序列化]")
            else:
                print("    无可用变量")
                
        except Exception:
            print("  \033[0;36m报错代码: [无法获取]\033[0m")
        tb = tb.tb_next
        step += 1
    print(f"\033[1;31m{'='*60}\033[0m")


def global_exception_handler(exc_type, exc_value, exc_traceback):
    print_code_chain(exc_traceback, exc_type, exc_value)


def asyncio_exception_handler(loop, context):
    exc = context.get("exception")
    if exc:
        global_exception_handler(type(exc), exc, exc.__traceback__)
    else:
        print("异步异常上下文：", context)


def set_exception_handler():
    sys.excepthook = global_exception_handler
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(asyncio_exception_handler)