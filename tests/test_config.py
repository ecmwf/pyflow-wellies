from io import StringIO
from os.path import join as pjoin

import pytest
import yaml

from wellies.config import concatenate_yaml_files
from wellies.config import overwrite_entries
from wellies.config import substitute_variables


class TestYamlParser:
    @pytest.fixture(autouse=True)
    def _get_workdir(self, tmpdir):
        self.wdir = tmpdir

    def _write(self, name, config):
        config_path = pjoin(self.wdir, f"{name}.yaml")
        with open(config_path, "w") as fin:
            content = StringIO(config).read()
            fin.write(content)
        return config_path

    def _run(self, configInput, expected):
        inputPath = self._write("config", configInput)

        with open(inputPath, "r") as file:
            options = yaml.load(file, Loader=yaml.SafeLoader)

        result = substitute_variables(options)

        assert result == expected

    def test_simple_level_configuration_variable_substitution(self):
        config_in = """
        user: dummy
        root: /scratch
        path: "{root}/{user}"

        myfile: "{path}/somefile.txt"
        """

        expected = {
            "user": "dummy",
            "root": "/scratch",
            "path": "/scratch/dummy",
            "myfile": "/scratch/dummy/somefile.txt",
        }

        self._run(config_in, expected)

    def test_nested_config_variable_substitution(self):
        config_in = """
        user: dummy
        root: /scratch
        path: "{root}/{user}"

        myfile: "{path}/somefile.txt"

        nested:
            key1:
                name: "{user}"
                path: "{path}"
                file: "{myfile}"
            key2:
                name: john
                root: /perm
                path: "{root}/{name}"
                file: "{path}/otherfile.txt"
        """

        expected = {
            "user": "dummy",
            "root": "/scratch",
            "path": "/scratch/dummy",
            "myfile": "/scratch/dummy/somefile.txt",
            "nested": {
                "key1": {
                    "name": "dummy",
                    "path": "/scratch/dummy",
                    "file": "/scratch/dummy/somefile.txt",
                },
                "key2": {
                    "name": "john",
                    "root": "/perm",
                    "path": "/perm/john",
                    "file": "/perm/john/otherfile.txt",
                },
            },
        }

        self._run(config_in, expected)

    def test_key_used_before_assingnment(self):
        config_in = """
        user: dummy
        root: /scratch
        myfile: "{path}/somefile.txt"

        path: "{root}/{user}"
        """

        with pytest.raises(KeyError):
            self._run(config_in, expected=None)

    def test_force_to_str(self):
        config_in = """
        a_int: 1
        a_int_str: "1"

        b_int: "{a_int}"
        b_int_str: "{a_int_str}"
        """
        expected = {
            "a_int": 1,
            "a_int_str": "1",
            "b_int": "1",
            "b_int_str": "1",
        }
        self._run(config_in, expected=expected)

    @pytest.mark.xfail(reason="Substution inside lists not supported")
    def test_replace_inside_list(self):
        config_in = """
        user: dummy
        root: /scratch
        paths: ["{root}/{user}", "/perm/dummy2"]

        all_vars:
          - "{root}"
          - "{user}"
        """

        expected = {
            "user": "dummy",
            "root": "/scratch",
            "paths": ["/scratch/dummy", "/perm/dummy2"],
            "all_vars": ["/scratch", "dummy"],
        }

        self._run(config_in, expected)

    def test_accept_general_assigns(self):
        config_in = """
        user: dummy
        age: 14
        height: 1.89
        surnames: ['foo', 'boo']
        surnames_again:
            - foo
            - boo
        """

        expected = {
            "user": "dummy",
            "age": 14,
            "height": 1.89,
            "surnames": ["foo", "boo"],
            "surnames_again": ["foo", "boo"],
        }

        self._run(config_in, expected)

    def test_replace_any_object_as_str(self):
        config_in = """
        user: dummy
        height: 1.89
        weight: 82
        surnames: ['foo', 'boo']

        family_name: "{surnames}"
        bmi_formula: "{weight}/{height}^2"

        nested:
            user: "{user}"
            surnames: "{surnames}"
            bmi_formula: "{weight}/{height}^2"
        """

        expected = {
            "user": "dummy",
            "height": 1.89,
            "weight": 82,
            "surnames": ["foo", "boo"],
            "family_name": "['foo', 'boo']",
            "bmi_formula": "82/1.89^2",
            "nested": {
                "user": "dummy",
                "surnames": "['foo', 'boo']",
                "bmi_formula": "82/1.89^2",
            },
        }

        self._run(config_in, expected)

    def test_concatenation(self):
        config_1 = """
        user: dummy
        """
        config_1_path = self._write("config_1", config_1)

        config_2 = """
        host: foo
        """
        config_2_path = self._write("config_2", config_2)

        config_3 = """
        root: bar
        """
        config_3_path = self._write("config_3", config_3)

        ref_options = {
            "user": "dummy",
            "host": "foo",
            "root": "bar",
        }
        options = concatenate_yaml_files(
            [config_1_path, config_2_path, config_3_path]
        )
        print(options)
        print(ref_options)
        assert options == ref_options

    def test_duplicates(self):
        config_1 = """
        user: dummy
        """
        config_1_path = self._write("config_1", config_1)

        config_2 = """
        user: foo
        """
        config_2_path = self._write("config_2", config_2)

        with pytest.raises(KeyError):
            concatenate_yaml_files([config_1_path, config_2_path])

    def test_overwrite_none(self):
        config = """
        user: dummy
        """
        config_path = self._write("config", config)
        with open(config_path, "r") as file:
            options = yaml.load(file, Loader=yaml.SafeLoader)

        overwrite_values = ""
        options = overwrite_entries(options, overwrite_values)

        ref_options = {"user": "dummy"}
        print(options)
        print(ref_options)
        assert options == ref_options

    def test_overwrite(self):
        config = """
        user: dummy
        """
        config_path = self._write("config", config)
        with open(config_path, "r") as file:
            options = yaml.load(file, Loader=yaml.SafeLoader)

        overwrite_values = ["user=foo"]
        options = overwrite_entries(options, overwrite_values)

        ref_options = {"user": "foo"}
        print(options)
        print(ref_options)
        assert options == ref_options

    def test_overwrite_nested(self):
        config = """
        data:
            key1: value1
            key2: value2
        """
        config_path = self._write("config", config)
        with open(config_path, "r") as file:
            options = yaml.load(file, Loader=yaml.SafeLoader)

        overwrite_values = ["data.key1=foo"]
        options = overwrite_entries(options, overwrite_values)

        ref_options = {"data": {"key1": "foo", "key2": "value2"}}
        print(options)
        print(ref_options)
        assert options == ref_options

    def test_invalid_variable_substitution(self):
        config_in = """
        user: dummy
        path: "{_FORTESTING}"
        """

        with pytest.raises(ValueError):
            self._run(config_in, expected=None)
