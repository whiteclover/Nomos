快速开始
++++++++++++++++


本文将会讲会你如何简单使用nomos编写测试。

#. 安装 nomos
#. 创建 nomos 测试
#. 执行nomos测试




安装 nomos
===================


要求python版本2.7+

你可以使用pip安装或者手动安装

.. code-block:: bash
    
    pip install nomos


如果使用开发模式，请使用git拷贝本项目，然后移动到项目根目录，在控制台执行开发模式安装:

.. code-block:: bash

    python setup.py develop


创建 nomos 测试
=====================================

创建一个 nomos 测试，文件名为 ``test.smoke``.


.. code-block:: txt

    [initialize]

    $status= 1
    $token ="token"


    [post json data]

    >> POST /post token=$token


    json << {
        deviceStatus: [
            {
                deviceId: 133
                status: $status
                content: @{resoure("file.txt")}
             }
        ]
    }


    json {
    
        args {
            token: $token
        }

        json {

            deviceStatus: [
                {
                    status = $status
                    deviceId: 133
                    deviceId != 134
                    deviceId > 132
                }
            ]
        }
    }



执行 nomos 测试
==========================


在控制台执行如下命令:

.. code-block:: bash
    
    python - m nomos    -url=http://httpbin.org   test.smoke
