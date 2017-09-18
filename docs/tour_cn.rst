Nomos入门
+++++++++++++++


Nomos 是借鉴JSON语义拓展的DSL超集，用于生成Python的单元测试，
内部使用reuqests做http交互。

定义测试类
=============

Nomos以类型为smoke的文件作为一个测试案例类。 比如 update_file.smoke 将会生成一个类名为 ``UploadFileTest`` 的测试类。

定义测试方法
=============

所有的测试方法 以中括号 ``[ 类名注解 ]``  为测试方法的方法区


.. code-block:: txt
    [item list]

    >> GET /item/list

    params {
        page=1
        size=10
        key=key
        content=content
    }

如上定义了一个 名叫 index的测试方法，然后向服务端发送了一个 路径为 ‘/’的get请求。

上面的代码最后将会被编译成类似下面流程的代码：
    
.. code-block:: python

    from nomos.http import HttpSession
    session = HttpSession("url prefix")
    res = session.get("/", params=dict(page=1
        size=10
        key="key"
        content="content"))



发送一个请求
===============


看到以 ``>>`` 指令 开始的DSL行， 这就是定义了一个 http 请求::

    >> METHOD  PATH  [PARAM1=ARG1, ...]

:METHOD: 为HTTP请求方法, 如 GET， POST，HEAD， PUT，DELETE等。
:PATH:  为请求路径后缀。 如 ``/item/list``
:[PARAM1=ARG1, ...]: 为url参数组合规则需要符合nomos语法，具体规则后面讲述 如： ``key=key page=10``


设置请求参数
===============


如果发送GET请求 可以在 ”>>“ 请求指令 路径后面 设置请求参数列表

另外可以通过


params 设置url参数


.. code-block:: txt 
    [item/list]

    >> GET /

    params {
        page=1
        size=10
        key=key
        content=content
    }


