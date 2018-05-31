Quick Start
++++++++++++++++

This Documentation will teach you how to build a simple test using nomos.

#. Installing nomos
#. Creating a nomos test
#. Running the test




Install nomos
===================


Requires python 2.7+ version.

You can install nomos with a single command using pip, type this into your terminal:


.. code-block:: bash
    
    pip install nomos

Develop mode, git clone the project, then move to the proejct directory, type this into your terminal:

.. code-block:: bash

    python setup.py develop


Creating a nomos test
=====================================

Writing code in file named ``test.smoke``.


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



Running the test
==========================

Type this into your terminal for running the test:


.. code-block:: bash
    
    python - m nomos    -url=http://httpbin.org   test.ns
