# freeIPA-users_migration_script
python script for user migration from freeIPA to freeIPA
<br><br><br><br>
_______
## usage: 
make sure you have installed python-freeipa via pip or system package manager
```pip install python-freeipa```

### export: 
```python freeIPA_userse_migrate.py export --server old_ipa.server.hostname --principal admin --password adminpassword --file users.json```

### import: 
```python freeIPA_userse_migrate.py export --server new_ipa.server.hostname --principal admin --password adminpassword --file users.json``` 



<br><br><br><br><br><br><br>

_______
#### Copyright 2025 Resistine

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

[Visit resistine](https://www.resistine.com)
