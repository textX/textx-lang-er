from os.path import join, dirname
from textx.metamodel import metamodel_from_file
from textx.model import parent_of_type, children_of_type
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


def parent_entity(obj):
    """
    Returns direct or indirect parent entity object if exists or None.
    """
    return parent_of_type(obj, "Entity")


def meta_name(obj):
    """
    Returns meta type name of the given object.
    """
    return obj.__class__.__name__


def is_entity_ref(attr):
    return meta_name(attr_type(attr)) == 'Entity'


def is_enum_ref(attr):
    return meta_name(attr_type(attr)) == 'Enum'


def attr_type(attr):
    """
    Returns attribute type.
    """
    return attr.type.type


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
    'positive': ConstraintType(None, 'positive', applies_to_attribute=True),
    'upper_case': ConstraintType(None, 'upper_case', applies_to_attribute=True),
    'lower_case': ConstraintType(None, 'lower_case', applies_to_attribute=True),
    'email': ConstraintType(None, 'email', applies_to_attribute=True),
}


def attribute_processor(attr):
    """
    Called for each attribute.
    """
    entity = parent_of_type(attr, "Entity")

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

    if not is_entity_ref(attr) and m.upper == '*':
        raise TextXSemanticError('Attribute "{}". Can\'t use '
                                 '* multiplicity for non-reference type.'
                                 .format(attr.name))
    # Check constraints
    for c in attr.constraints:
        if not c.type.applies_to_attribute:
            raise TextXSemanticError('In "{}.{}". Constraint "{}" can not '
                                     'be applied to attribute.'
                                     .format(entity.name, attr.name,
                                             c.type.name))


def entity_processor(ent):
    """
    Validates entities.
    """

    # Check constraints
    for c in ent.constraints:
        if not c.type.applies_to_entity:
            raise TextXSemanticError('In Entity "{}". Constraint "{}" can not '
                                     'be applied to Entity.'
                                     .format(ent.name, c.type.name))

    # Collect all referenced entities without other side attr name spec.
    referenced_entities = set()
    attr_names = set()
    for attr in children_of_type(ent, "Attribute"):
        if is_entity_ref(attr):
            if not attr.ref or not attr.ref.other_side:
                if id(attr_type(attr)) in referenced_entities:
                    raise TextXSemanticError(
                        'In entity "{}". Multiple references to Entity "{}" '
                        'without other side '
                        'attr name specification. Specify other side name '
                        'using "<->" syntax.'.format(parent_entity(attr).name,
                                                     attr_type(attr).name))
                referenced_entities.add(id(attr_type(attr)))

        if attr.name in attr_names:
            raise TextXSemanticError('Attribute "{}" defined more than once for'
                                     ' entity {}.'.format(attr.name, ent.name))
        attr_names.add(attr.name)

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
                'Attribute': attribute_processor,
                'Entity': entity_processor,
             })
    return _meta
