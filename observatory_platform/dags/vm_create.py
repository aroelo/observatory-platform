# Copyright 2020 Curtin University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Author: Aniek Roelofs

from datetime import datetime

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.python_operator import ShortCircuitOperator
from observatory_platform.telescopes.terraform import TerraformTelescope


default_args = {
    "owner": "airflow",
    "start_date": datetime(2020, 7, 1)
}


with DAG(dag_id=TerraformTelescope.DAG_ID_CREATE_VM, schedule_interval="@weekly", default_args=default_args,
         catchup=False, max_active_runs=1) as dag:
    # Check that dependencies exist before starting
    check = PythonOperator(
        task_id=TerraformTelescope.TASK_ID_CHECK_DEPENDENCIES,
        python_callable=TerraformTelescope.check_dependencies,
    )

    # If vm is already on, stop DAG
    vm_status = ShortCircuitOperator(
        task_id=TerraformTelescope.TASK_ID_VM_STATUS,
        python_callable=TerraformTelescope.get_variable_create,
        provide_context=True
    )

    # Update terraform variable vm_create to True
    var_create = PythonOperator(
        task_id=TerraformTelescope.TASK_ID_VAR_UPDATE,
        python_callable=TerraformTelescope.update_terraform_variable,
        provide_context=True
    )

    # Run terraform configuration
    run_terraform = PythonOperator(
        task_id=TerraformTelescope.TASK_ID_RUN,
        python_callable=TerraformTelescope.terraform_run,
        provide_context=True
    )

    # Check status of terraform run
    check_run_status = PythonOperator(
        task_id=TerraformTelescope.TASK_ID_RUN_STATUS,
        python_callable=TerraformTelescope.check_terraform_run_status,
        provide_context=True
    )

    check >> vm_status >> var_create >> run_terraform >> check_run_status
