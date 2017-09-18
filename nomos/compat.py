#!/usr/bin/env python
#
# Copyright 2017 Nomos
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


try:
    # python 3.5+
    import importlib.util

    def import_module_from_file(name, path):

        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

except:
    try:
        # python 3.4...
        from importlib.machinery import SourceFileLoader

        def import_module_from_file(name, path):
            return SourceFileLoader(name, path).load_module()
    except:
        # python 2.7
        import imp

        def import_module_from_file(name, path):
            return imp.load_source(name, path)
