from io import StringIO
from os.path import join as pjoin

import pytest
import yaml

from wellies.config import concatenate_yaml_files
from wellies.config import nested_set
from wellies.config import overwrite_entries
from wellies.config import substitute_variables
from wellies.exceptions import WelliesConfigurationError


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

    def test_key_used_before_assignment(self):
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

    @pytest.mark.xfail(
        reason="Substution inside lists not supported", strict=True
    )
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

    def test_nested_values_do_not_shadow_parent_scope(self):
        options = {
            "name": "dummy",
            "nested": {"name": "foo"},
            "path": "/scratch/{name}",
        }

        result = substitute_variables(options)

        assert result["nested"]["name"] == "foo"
        assert result["path"] == "/scratch/dummy"

    def test_nested_sibling_scopes_are_isolated(self):
        options = {
            "name": "global",
            "first": {"name": "local", "path": "/scratch/{name}"},
            "second": {"path": "/scratch/{name}"},
        }

        result = substitute_variables(options)

        assert result["first"]["name"] == "local"
        assert result["first"]["path"] == "/scratch/local"
        assert result["second"]["path"] == "/scratch/global"

    def test_nested_values_are_not_parent_substitution_sources(self):
        options = {
            "nested": {"name": "foo"},
            "path": "/scratch/{name}",
        }

        with pytest.raises(
            KeyError,
            match='Variable substitution failed: Key "name" used before assignment',
        ):
            substitute_variables(options)

    def test_merged_ecflow_variables_ignore_nested_scope_values(self):
        config_1 = """
        name: dummy
        ecflow_variables:
            LABEL: "{name}"
        """
        config_1_path = self._write("config_1", config_1)

        config_2 = """
        nested:
            name: garbage
        ecflow_variables:
            DATADIR: "/scratch/{name}"
        """
        config_2_path = self._write("config_2", config_2)

        options = concatenate_yaml_files([config_1_path, config_2_path])
        result = substitute_variables(options)

        assert result["ecflow_variables"] == {
            "LABEL": "dummy",
            "DATADIR": "/scratch/dummy",
        }

    def test_ecflow_variable_can_reference_key_from_later_file(self):
        # Documents current behavior: ecflow_variables are substituted after all
        # ordinary top-level keys, irrespective of which file defines those keys.
        # Revisit this test if stricter cross-file dependency rules are introduced.
        config_1 = """
        ecflow_variables:
            LABEL: "{name}"
        """
        config_1_path = self._write("config_1", config_1)

        config_2 = """
        name: foo
        """
        config_2_path = self._write("config_2", config_2)

        options = concatenate_yaml_files([config_1_path, config_2_path])
        result = substitute_variables(options)

        assert result["ecflow_variables"]["LABEL"] == "foo"

    def test_duplicate_ecflow_variables_use_last_value(self):
        # Duplicate ecFlow variables currently use last-wins semantics, unlike
        # ordinary top-level keys. Stricter validation may be preferable later.
        config_1 = """
        ecflow_variables:
            LABEL: first
        """
        config_1_path = self._write("config_1", config_1)

        config_2 = """
        ecflow_variables:
            LABEL: second
        """
        config_2_path = self._write("config_2", config_2)

        options = concatenate_yaml_files([config_1_path, config_2_path])
        result = substitute_variables(options)

        assert result["ecflow_variables"]["LABEL"] == "second"

    def test_ecflow_variable_can_reference_earlier_ecflow_variable(self):
        # Merged ecFlow variables share a substitution scope and are resolved in
        # insertion order. Stricter dependency validation may be preferable later.
        config_1 = """
        ecflow_variables:
            ROOT: /scratch
        """
        config_1_path = self._write("config_1", config_1)

        config_2 = """
        ecflow_variables:
            DATADIR: "{ROOT}/data"
        """
        config_2_path = self._write("config_2", config_2)

        options = concatenate_yaml_files([config_1_path, config_2_path])
        result = substitute_variables(options)

        assert result["ecflow_variables"] == {
            "ROOT": "/scratch",
            "DATADIR": "/scratch/data",
        }

    def test_ecflow_variable_cannot_reference_later_ecflow_variable(self):
        # Forward references within the merged ecFlow mapping currently fail
        # because its entries are substituted in insertion order.
        config_1 = """
        ecflow_variables:
            DATADIR: "{ROOT}/data"
        """
        config_1_path = self._write("config_1", config_1)

        config_2 = """
        ecflow_variables:
            ROOT: /scratch
        """
        config_2_path = self._write("config_2", config_2)

        options = concatenate_yaml_files([config_1_path, config_2_path])

        with pytest.raises(
            KeyError,
            match='Variable substitution failed: Key "ROOT" used before assignment',
        ):
            substitute_variables(options)

    def test_ecflow_variables_merge_order_substitution(self):
        # An ecflow_variable defined in a later file can reference a normal
        # key from that file, even if an earlier file also set ecflow_variables.
        config_1 = """
        ecflow_variables:
            FOO: bar
        """
        config_1_path = self._write("config_1", config_1)

        config_2 = """
        root: /scratch
        ecflow_variables:
            DATADIR: "{root}/data"
        """
        config_2_path = self._write("config_2", config_2)

        options = concatenate_yaml_files([config_1_path, config_2_path])
        result = substitute_variables(options)

        assert result["ecflow_variables"] == {
            "FOO": "bar",
            "DATADIR": "/scratch/data",
        }

    def test_duplicate_null_top_level_key_raises(self):
        config_1 = """
        name: null
        """
        config_1_path = self._write("config_1", config_1)

        config_2 = """
        name: foo
        """
        config_2_path = self._write("config_2", config_2)

        with pytest.raises(KeyError, match="Following keys found"):
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


class TestOverwriteEntries:
    """Tests for the ``-s KEY=VALUE`` command line override mechanism.

    The override is applied by ``overwrite_entries`` which delegates the
    per-key assignment to ``nested_set``. ``nested_set`` coerces the (always
    string) command line value to the type of the value already present in the
    configuration.
    """

    def test_overwrite_falsy_bool(self):
        # A ``False`` value in the config used to be interpreted as "no value"
        # because of a truthiness check, raising a TypeError.
        options = {"flag": False}
        result = overwrite_entries(options, ["flag=true"])
        assert result == {"flag": True}
        assert result["flag"] is True

    def test_overwrite_true_with_false(self):
        # bool("false") is True, so a naive coercion would keep the value True.
        options = {"flag": True}
        result = overwrite_entries(options, ["flag=false"])
        assert result == {"flag": False}
        assert result["flag"] is False

    def test_overwrite_falsy_int(self):
        options = {"count": 0}
        result = overwrite_entries(options, ["count=5"])
        assert result == {"count": 5}
        assert isinstance(result["count"], int)

    def test_overwrite_falsy_float(self):
        options = {"ratio": 0.0}
        result = overwrite_entries(options, ["ratio=1.5"])
        assert result == {"ratio": 1.5}
        assert isinstance(result["ratio"], float)

    def test_overwrite_empty_string(self):
        options = {"name": ""}
        result = overwrite_entries(options, ["name=hello"])
        assert result == {"name": "hello"}

    def test_overwrite_none_value(self):
        # A null value in yaml gives no type information, the override should
        # be kept as a plain string rather than crashing.
        options = {"name": None}
        result = overwrite_entries(options, ["name=hello"])
        assert result == {"name": "hello"}

    def test_overwrite_preserves_int_type(self):
        options = {"count": 10}
        result = overwrite_entries(options, ["count=20"])
        assert result == {"count": 20}
        assert isinstance(result["count"], int)

    def test_overwrite_preserves_float_type(self):
        options = {"ratio": 1.0}
        result = overwrite_entries(options, ["ratio=2.5"])
        assert result == {"ratio": 2.5}
        assert isinstance(result["ratio"], float)

    def test_overwrite_falsy_nested(self):
        options = {"data": {"flag": False, "other": "keep"}}
        result = overwrite_entries(options, ["data.flag=true"])
        assert result == {"data": {"flag": True, "other": "keep"}}

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
            ("off", False),
        ],
    )
    def test_overwrite_bool_representations(self, raw, expected):
        options = {"flag": True}
        result = overwrite_entries(options, [f"flag={raw}"])
        assert result["flag"] is expected

    def test_overwrite_invalid_bool_raises(self):
        options = {"flag": False}
        with pytest.raises(WelliesConfigurationError):
            overwrite_entries(options, ["flag=maybe"])

    def test_overwrite_multiple_values(self):
        options = {"flag": False, "count": 0, "name": "old"}
        result = overwrite_entries(
            options, ["flag=true", "count=3", "name=new"]
        )
        assert result == {"flag": True, "count": 3, "name": "new"}

    def test_overwrite_none_values_noop(self):
        options = {"flag": False}
        result = overwrite_entries(options, None)
        assert result == {"flag": False}

    def test_overwrite_new_key_kept_as_string(self):
        # Setting a key that does not exist yet has no type information, so the
        # value is kept as a plain string.
        options = {"existing": "value"}
        result = overwrite_entries(options, ["brand_new=42"])
        assert result == {"existing": "value", "brand_new": "42"}

    def test_nested_set_falsy_bool_directly(self):
        dic = {"flag": False}
        nested_set(dic, ["flag"], "true")
        assert dic["flag"] is True
