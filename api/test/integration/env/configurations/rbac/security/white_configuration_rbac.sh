#!/usr/bin/env bash

sed -i 's,"mode": \("white"\|"black"\),"mode": "white",g' /var/ossec/framework/python/lib/python3.7/site-packages/api-4.0.0-py3.7.egg/api/configuration.py
sed -i "s:    # policies = RBAChecker.run_testing():    policies = RBAChecker.run_testing():g" /var/ossec/framework/python/lib/python3.7/site-packages/wazuh-4.0.0-py3.7.egg/wazuh/rbac/preprocessor.py
permissions='[{"actions":["security:read"],"resources":["user:id:administrator","user:id:normal","user:id:python","user:id:guest","role:id:*"],"effect":"allow"},{"actions":["security:read"],"resources":["policy:id:*"],"effect":"deny"},{"actions":["security:update"],"resources":["user:id:*"],"effect":"deny"},{"actions":["security:update"],"resources":["role:id:11","role:id:10","role:id:13","policy:id:18","policy:id:13","policy:id:15"],"effect":"allow"},{"actions":["security:update"],"resources":["policy:id:18","policy:id:13"],"effect":"deny"},{"actions":["security:delete"],"resources":["user:id:guest","user:id:normal","user:id:wazuh-wui","policy:id:*"],"effect":"allow"},{"actions":["security:delete"],"resources":["policy:id:*","role:id:*"],"effect":"deny"},{"actions":["security:create_user"],"resources":["*"],"effect":"deny"},{"actions":["security:create"],"resources":["*"],"effect":"allow"}]'
awk -v var="${permissions}" '{sub(/testing_policies = \[\]/, "testing_policies = " var)}1' /var/ossec/framework/python/lib/python3.7/site-packages/wazuh-4.0.0-py3.7.egg/wazuh/rbac/auth_context.py >> /var/ossec/framework/python/lib/python3.7/site-packages/wazuh-4.0.0-py3.7.egg/wazuh/rbac/auth_context1.py
cat /var/ossec/framework/python/lib/python3.7/site-packages/wazuh-4.0.0-py3.7.egg/wazuh/rbac/auth_context1.py > /var/ossec/framework/python/lib/python3.7/site-packages/wazuh-4.0.0-py3.7.egg/wazuh/rbac/auth_context.py
