from defines import description

def get_string(id,*args,**kwargs):
    str_format = description.cn_desc[id]
    return str_format.format(*args,**kwargs)

def get_string_wecom(id,*args,**kwargs):
    str_format = description.wecom_desc[id]
    return str_format.format(*args,**kwargs)

