from os.path import join, dirname
from textx.metamodel import metamodel_from_file
from textx.exceptions import TextXSemanticError

__import__ = ['meta']


_meta = None


def get_constraint(obj, name):
    """
    Get a constraint vith the given name for the given object.
    If constraint is not specified for the object returns None.
    """
    for c in obj.constraints:
        if c.type.name == name:
            return c


class Entity(object):
    def __init__(self, parent, name, label=None, extends=None,
                 constraints=None, desc=None, attributes=None,
                 compartments=None):
        self.parent = parent
        self.name = name
        self.label = label
        self.extends = extends
        self.constraints = [] if constraints is None else constraints
        self.desc = desc
        self.attributes = [] if attributes is None else attributes
        self.compartments = [] if compartments is None else compartments

    @property
    def all_attributes(self):
        for attr in self.attributes:
            yield attr
        for comp in self.compartments:
            for attr in comp.attributes:
                yield attr


class DataType(object):
    def __init__(self, parent, name):
        self.parent = parent
        self.name = name


class ConstraintType(object):
    def __init__(self, parent, name, parameter_types=None,
                 applies_to_attribute=False, applies_to_entity=False):
        self.parent = parent
        self.name = name
        self.parameter_types = [] \
            if parameter_types is None else parameter_types

        if not applies_to_attribute and not applies_to_entity:
            self.applies_to_attribute = True
            self.applies_to_entity = True
        else:
            self.applies_to_attribute = applies_to_attribute
            self.applies_to_entity = applies_to_entity


class Multiplicity(object):
    def __init__(self, parent, lower, upper=1):
        self.parent = parent
        self.lower = lower
        self.upper = upper


data_types = {
    'int': DataType(None, 'int'),
    'string': DataType(None, 'string'),
    'time': DataType(None, 'time'),
    'date': DataType(None, 'date'),
    'float': DataType(None, 'float'),
    'decimal': DataType(None, 'decimal'),
    'bool': DataType(None, 'bool')
}

constraints = {
    'unique': ConstraintType(None, 'unique', applies_to_attribute=True),
    'ordered': ConstraintType(None, 'ordered', applies_to_attribute=True),
    'dbname': ConstraintType(None, 'dbname', applies_to_attribute=True,
                             applies_to_entity=True),
    'fk_cols': ConstraintType(None, 'fk_names', applies_to_attribute=True),
    'positive': ConstraintType(None, 'positive', applies_to_attribute=True),
    'upper_case': ConstraintType(None, 'upper_case', applies_to_attribute=True),
    'lower_case': ConstraintType(None, 'lower_case', applies_to_attribute=True),
    'email': ConstraintType(None, 'email', applies_to_attribute=True),
}


def attribute_processor(attr):
    """
    Called for each attribute.
    """

    if attr.multiplicity is None:
        # Default multiplicity is 1,1
        attr.multiplicity = Multiplicity(attr, lower=1, upper=1)
    elif attr.multiplicity.upper is None:

        # If only * is given it is must be the upper limit.
        if attr.multiplicity.lower == '*':
            attr.multiplicity.lower = 0
            attr.multiplicity.upper = '*'
        else:
            # Default upper multiplicity is 1
            attr.multiplicity.upper = 1

    # Sanity checks
    m = attr.multiplicity
    if m.lower not in [0, 1]:
        raise TextXSemanticError('Attribute "{}". Lower bound must be 0 or 1.'
                                 .format(attr.name))
    if type(m.upper) is int and m.upper != 1:
        raise TextXSemanticError('Attribute "{}". Upper bound must be 1 or *.'.
                                 format(attr.name))
    if m.upper == '*' and attr.id:
        raise TextXSemanticError('Attribute "{}". Key attributes can\'t have '
                                 '* multiplicity.'.format(attr.name))


def main():
    """
    Entity-Relationship language.
    """
    global _meta

    builtins = dict(data_types, **constraints)

    if _meta is None:
        _meta = metamodel_from_file(
            join(dirname(__file__), 'er.tx'),
            autokwd=True,
            classes=[Entity, DataType, ConstraintType, Multiplicity],
            builtins=builtins
        )
        _meta.register_obj_processors(
            {
                'Attribute': attribute_processor
             })
    return _meta
