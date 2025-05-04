# -*- coding: utf-8 -*-
# /usr/bin/env python3

# 中文: 从具体的 crud 文件中导入实例, 使其可以通过 app.crud.xxx 访问
# English: Import instances from specific crud files so they can be accessed via app.crud.xxx
from .crud_link import link
from .crud_history import history_log
from .crud_user import user
from .crud_password_reset import password_reset_token
