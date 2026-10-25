"""Auditable coordinate contract for approved travel pixels, never replacement artwork."""
CANVAS = (256, 256)
ANCHOR = (128, 224)
BODY_HEIGHT = 208
VIEWS = {
    'front': {'window': [160, 0, 610, 855], 'side_bag_dx': 0},
    'left': {'window': [650, 0, 1110, 855], 'side_bag_dx': 0},
    'right': {'window': [1180, 0, 1630, 855], 'side_bag_dx': 2},
}
# L/R in part IDs mean screen-left/right in each independently supplied view.
# Vertices are in the normalized 256px canvas, before animation transforms.
PARTS = {
    'head': {'parent': 'root', 'pivot': [128, 97], 'poly': [[0, 0], [256, 0], [256, 100], [0, 100]], 'common': True},
    'satchel': {'parent': 'torso', 'pivot': [145, 138], 'poly': [[138, 135], [151, 133], [159, 140], [160, 155], [156, 164], [141, 161]]},
    'upper_arm_l': {'parent': 'torso', 'pivot': [105, 106], 'poly': [[96, 99], [113, 103], [109, 128], [104, 142], [85, 143], [88, 119]]},
    'forearm_hand_l': {'parent': 'upper_arm_l', 'pivot': [98, 134], 'poly': [[85, 129], [105, 130], [108, 155], [102, 168], [88, 165], [85, 147]]},
    'upper_arm_r': {'parent': 'torso', 'pivot': [151, 106], 'poly': [[146, 103], [160, 98], [170, 120], [174, 142], [154, 144], [146, 126]]},
    'forearm_hand_r': {'parent': 'upper_arm_r', 'pivot': [160, 135], 'poly': [[153, 130], [175, 129], [174, 157], [168, 169], [152, 165], [151, 148]]},
    'shin_foot_l': {'parent': 'thigh_l', 'pivot': [115, 184], 'poly': [[0, 178], [129, 178], [129, 256], [0, 256]]},
    'shin_foot_r': {'parent': 'thigh_r', 'pivot': [141, 184], 'poly': [[126, 178], [256, 178], [256, 256], [126, 256]]},
    'thigh_l': {'parent': 'root', 'pivot': [116, 155], 'poly': [[0, 151], [129, 151], [129, 189], [0, 189]]},
    'thigh_r': {'parent': 'root', 'pivot': [141, 155], 'poly': [[126, 151], [256, 151], [256, 189], [126, 189]]},
    'jacket_flap': {'parent': 'torso', 'pivot': [105, 143], 'poly': [[97, 142], [112, 142], [113, 158], [97, 158]]},
    'collar': {'parent': 'torso', 'pivot': [128, 103], 'poly': [[108, 98], [150, 98], [153, 110], [136, 117], [112, 111]]},
    'torso': {'parent': 'root', 'pivot': [128, 155], 'poly': None},
    'expression_neutral': {'parent': 'head', 'pivot': [128, 80], 'poly': [[104, 66], [153, 66], [153, 95], [104, 95]], 'common': True, 'overlay': True},
}
# Partition first; joints are explicitly extended with source pixels only.
OVERLAPS = {
    'upper_arm_l': [([98, 134], 5)], 'forearm_hand_l': [([98, 134], 5)],
    'upper_arm_r': [([160, 135], 5)], 'forearm_hand_r': [([160, 135], 5)],
    'thigh_l': [([115, 184], 5)], 'shin_foot_l': [([115, 184], 5)],
    'thigh_r': [([141, 184], 5)], 'shin_foot_r': [([141, 184], 5)],
    'torso': [([105, 106], 6), ([151, 106], 6), ([116, 155], 6), ([141, 155], 6)],
}
DRAW_ORDER = ['thigh_l', 'shin_foot_l', 'thigh_r', 'shin_foot_r', 'upper_arm_l',
              'forearm_hand_l', 'upper_arm_r', 'forearm_hand_r', 'torso',
              'jacket_flap', 'satchel', 'collar', 'head', 'expression_neutral']
# Exact world station ground RGB from firmware/main/adv_ui_map.c WORLD.
WORLDS = {'town': '#f6e2b4', 'deep_sea': '#061434'}
ANIMATION_SPECS = {
    'idle': {'facing':'front','count':8,'height':48,'loop':True},
    'walk_left': {'facing':'left','count':8,'height':48,'loop':True},
    'walk_right': {'facing':'right','count':8,'height':48,'loop':True},
    'cheer': {'facing':'front','count':8,'height':72,'loop':False},
    'sad': {'facing':'front','count':6,'height':48,'loop':False},
    'welcome': {'facing':'front','count':16,'height':120,'loop':True,'runtime_visible_colours':48},
}
ANIMS = [(name,spec['facing']) for name,spec in ANIMATION_SPECS.items()]
