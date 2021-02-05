from docker import DockerClient
from docker import APIClient

from simple_switch.simple_switch_runner import SimpleSwitchDocker

from shutil import copytree
from shutil import rmtree
import os


def compile_p4(source_dir, main):
    name = '.'.join(main.split('.')[:-1])
    tmp_dir = '/tmp/' + name
    out_dir = tmp_dir + '/out'
    p4info = os.path.join(out_dir, f'{name}.p4info.txt')

    if os.path.exists(tmp_dir):
        print(f'deleting {tmp_dir}')
        rmtree(tmp_dir)
    
    copytree(source_dir, tmp_dir)
    compile_command = f'p4c {main} -o {out_dir} -I{tmp_dir} --p4runtime-files={p4info}'.split()
    print(compile_command)
    client = DockerClient(base_url="unix://var/run/docker.sock", version='auto')
    x = None

    container = client.containers.run(
        SimpleSwitchDocker.CONTAINER,
        compile_command,
        working_dir=tmp_dir,
        volumes={tmp_dir: {'bind': tmp_dir, 'mode': 'rw'}},
        detach=True
    )

    status = container.wait()

    logs = []
    print()
    for line in container.logs(stream=True):
        line = line.decode('utf-8').replace('\n', '')
        print(line)
    print()
    container.remove()

    if status != 0:
        raise Exception('Error running compile')

    result_dir = os.path.join(source_dir, 'out')
    compiled = os.path.join(result_dir, f'{name}.json')

    if os.path.exists(result_dir):
        rmtree(result_dir)
    copytree(out_dir, result_dir)

    return compiled, p4info