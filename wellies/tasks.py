import re

import pyflow as pf


class EcfResourcesTask(pf.Task):
    """Class that automatically sets ecflow variables for each submit_arguments
    key:value pair as they are in the host configuration file.

    Using variables makes it easier to change job directives values after
    deployment and using ecflow api.

    Also, inspects task tree for identical key:values pairs defined in higher
    levels to avoid creating duplicated variable at every level.

    :Attention: Following names are protected and will not be touched:
      - STHOST
      - ECF_*

    !!! Attention
        Following names will generate variables with other names than config
        keys:
        - TMPDIR -> SSDTMP
    """

    protected_list = [
        "^STHOST$",
        "^ECF_",
    ]
    replacements = {
        "TMPDIR": "SSDTMP",
        "TIME": "TIMEOUT",
    }

    def __init__(self, *, submit_arguments, **kwargs):
        # init with values as they are
        submit_args = submit_arguments.copy()
        # update variable lists with values set on submit_arguments config
        new_vars = kwargs.pop("variables", {})
        new_vars.update(
            {
                self.replacements.get(k.upper(), k.upper()): v
                for k, v in submit_args.items()
                if not self._is_protected(k)
            }
        )
        # replace non-protected keys by ecf_variables
        submit_args.update(
            {
                k: f"%{self.replacements.get(k.upper(), k.upper())}%"
                for k in submit_args.keys()
                if not self._is_protected(k)
            }
        )

        super().__init__(
            variables=new_vars, submit_arguments=submit_args, **kwargs
        )

        # after node is created, if variable in parent node with same value,
        # remove from task
        for key, val in new_vars.items():
            try:
                parent_val = self._parent_lookup(key)
            except AttributeError:
                pass
            else:
                if val == parent_val:
                    var_node = [v for v in self.variables if v.name == key][0]
                    self.remove_node(var_node)

    def _is_protected(self, key):
        for protected in self.protected_list:
            if (
                re.search(protected, key.strip().lstrip(), re.IGNORECASE)
                is not None
            ):
                return True
        return False

    def _parent_lookup(self, name):
        parent = self.parent
        if name in parent._nodes:
            return parent._nodes[name].value
        return parent.parent.lookup_variable(name)
