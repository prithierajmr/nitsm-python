"""Code Module API"""

import functools
import inspect

from .enums import Capability, InstrumentTypeIdConstants
from .tsmcontext import SemiconductorModuleContext

__all__ = ["SemiconductorModuleContext", "Capability", "InstrumentTypeIdConstants", "code_module"]


# noinspection PyPep8Naming
class code_module:  # noqa: N801
    """This function decorator wraps the ISemiconductorModuleContext
    win32com.client.dynamic.CDispatch object passed from the Semiconductor Multi Test step into a
    nitsm.codemoduleapi.SemiconductorModuleContext object prior to calling the decorated function.
    """

    def __init__(self, func):
        """Converts a function into a TSM code module.

        The Semiconductor Multi Test step must pass the Step.SemiconductorModuleContext property to
        the code module as the first positional argument.
        """
        self._func = func
        self._signature = inspect.signature(func)
        functools.update_wrapper(self, func)

    def __get__(self, instance, owner):
        """Binds the code module to an object or class."""
        func = self._func.__get__(instance, owner)
        return type(self)(func)

    def __call__(self, *args, **kwargs):
        """Calls the code module."""
        bound_arguments = self._signature.bind(*args, **kwargs)
        arguments_iter = iter(bound_arguments.arguments.items())

        # find potential argument that could be the tsm context
        try:
            argument = next(arguments_iter)  # get first argument
            if inspect.isclass(argument[1]):  # class method check
                argument = next(arguments_iter)  # move to second argument
        except StopIteration:
            # Fallback: look for tsm context in kwargs by name
            for key in ("context", "tsm_context", "SemiConductorModuleContext"):
                if key in bound_arguments.arguments:
                    argument = (key, bound_arguments.arguments[key])
                    break
            else:
                raise TypeError(
                    (
                        "The number of arguments to the code module is less than expected. It must "
                        "accept as it's first argument the Semiconductor Module context passed from "
                        "TestStand or another code module or it should be passed as a keyword argument,"
                        " with keywords - 'context', 'tsm_context', or 'SemiConductorModuleContext'.",
                    )
                )

        # attempt to wrap argument in a SemiconductorModuleContext object
        argument_name, argument_value = argument
        if not isinstance(argument_value, SemiconductorModuleContext):
            try:
                argument_value = SemiconductorModuleContext(argument_value)
            except Exception:
                class_name = type(argument_value).__name__
                raise ValueError(
                    f"Failed to convert Semiconductor Module context from class '{class_name}'.",
                )
            bound_arguments.arguments[argument_name] = argument_value

        return self._func(*bound_arguments.args, **bound_arguments.kwargs)
