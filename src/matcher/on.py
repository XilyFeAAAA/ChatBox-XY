from src.model import MessageType
from .matcher import Matcher
from .rule import Rule, startswith, endswith, fullmatch, command, keyword, regex

def on_message(*args, **kwargs):
    kwargs.setdefault("type", MessageType.Text)
    def decorator(func):
        func.__matcher__ = Matcher.new(func, *args, **kwargs)
        return func
    return decorator


def on_startswith(
    text: str,
    rules: list[Rule] = [],
    ignorecase: bool = False,
    **kwargs
):
    def decorator(func):
        Matcher.new(func, rules=[startswith(text, ignorecase), *rules], **kwargs)
        return func
    return decorator


def on_endswith(
    text: str,
    rules: list[Rule] = [],
    ignorecase: bool = False,
    **kwargs
):
    def decorator(func):
        Matcher.new(func, rules=[endswith(text, ignorecase), *rules], **kwargs)
        return func
    return decorator


def on_fullmatch(
    text: str,
    rules: list[Rule] = [],
    ignorecase: bool = False,
    **kwargs
):
    def decorator(func):
        Matcher.new(func, rules=[fullmatch(text, ignorecase), *rules], **kwargs)
        return func
    return decorator


def on_keyword(
    keywords: set[str],
    rules: list[Rule] = [],
    **kwargs
):
    def decorator(func):
        Matcher.new(func, rules=[keyword(keywords), *rules], **kwargs)
        return func
    return decorator


def on_command(
    cmd: str,
    rules: list[Rule] = [],
    aliases: set[str] = set(),
    force_whitespace: bool = False,
    **kwargs
):
    def decorator(func):
        commands = {cmd} | aliases
        Matcher.new(func, rules=[command(*commands, force_whitespace), *rules], **kwargs)
        return func
    return decorator


def on_regex(
    patterns: list[str],
    rules: list[Rule] = [],
    flags: int = 0,
    **kwargs
):
    """
    注册一个基于正则表达式的Matcher
    :param pattern: 正则表达式字符串
    :param rules: 其他附加规则
    :param flags: re模块的flags参数
    :param kwargs: 其他Matcher参数
    """
    def decorator(func):
        Matcher.new(func, rules=[regex(patterns, flags), *rules], **kwargs)
        return func
    return decorator