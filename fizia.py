import pygame
import pymunk
import pymunk.pygame_util
import math

# تهيئة Pygame و Pymunk
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 24)

space = pymunk.Space()
space.gravity = (0, 2000)  # جاذبية واقعية
draw_options = pymunk.pygame_util.DrawOptions(screen)

# إنشاء الجدران لمنع الجسم من الخروج
def create_walls():
    thickness = 10
    walls = [
        pymunk.Segment(space.static_body, (0, 0), (WIDTH, 0), thickness),
        pymunk.Segment(space.static_body, (0, HEIGHT), (WIDTH, HEIGHT), thickness),
        pymunk.Segment(space.static_body, (0, 0), (0, HEIGHT), thickness),
        pymunk.Segment(space.static_body, (WIDTH, 0), (WIDTH, HEIGHT), thickness),
    ]
    for wall in walls:
        wall.elasticity = 0.5
        wall.friction = 1.0
        space.add(wall)

create_walls()

# إنشاء الجسم البشري
def create_human(pos):
    bodies, shapes, joints = [], [], []

    # الرأس
    head_radius = 20
    mass_head = 1.2
    head_body = pymunk.Body(mass_head, pymunk.moment_for_circle(mass_head, 0, head_radius))
    head_body.position = pos[0], pos[1]
    head_shape = pymunk.Circle(head_body, head_radius)
    head_shape.friction = 1.0
    space.add(head_body, head_shape)
    bodies.append(head_body)
    shapes.append(head_shape)

    # الجذع
    torso_size = (40, 80)
    mass_torso = 2.0
    torso_body = pymunk.Body(mass_torso, pymunk.moment_for_box(mass_torso, torso_size))
    torso_body.position = pos[0], pos[1] + 60
    torso_shape = pymunk.Poly.create_box(torso_body, torso_size)
    torso_shape.friction = 1.0
    space.add(torso_body, torso_shape)
    bodies.append(torso_body)
    shapes.append(torso_shape)

    # الرقبة
    neck_joint = pymunk.PivotJoint(head_body, torso_body, (pos[0], pos[1] + 20))
    neck_limit = pymunk.RotaryLimitJoint(head_body, torso_body, -0.4, 0.4)
    space.add(neck_joint, neck_limit)
    joints += [neck_joint, neck_limit]

    # الأذرع
    arm_size = (15, 35)
    mass_arm = 1.0
    arm_offset_x = 30
    arm_offset_y = 40

    for side in [-1, 1]:
        # الذراع العلوي
        upper_arm_body = pymunk.Body(mass_arm, pymunk.moment_for_box(mass_arm, arm_size))
        upper_arm_body.position = pos[0] + side * arm_offset_x, pos[1] + arm_offset_y
        upper_arm_shape = pymunk.Poly.create_box(upper_arm_body, arm_size)
        upper_arm_shape.friction = 1.0
        space.add(upper_arm_body, upper_arm_shape)
        bodies.append(upper_arm_body)
        shapes.append(upper_arm_shape)

        # الساعد
        lower_arm_body = pymunk.Body(mass_arm, pymunk.moment_for_box(mass_arm, arm_size))
        lower_arm_body.position = upper_arm_body.position[0], upper_arm_body.position[1] + 35
        lower_arm_shape = pymunk.Poly.create_box(lower_arm_body, arm_size)
        lower_arm_shape.friction = 1.0
        space.add(lower_arm_body, lower_arm_shape)
        bodies.append(lower_arm_body)
        shapes.append(lower_arm_shape)

        # مفاصل
        shoulder = pymunk.PivotJoint(torso_body, upper_arm_body, (pos[0] + side * 20, pos[1] + 20))
        elbow = pymunk.PivotJoint(upper_arm_body, lower_arm_body, (0, 17), (0, -17))
        shoulder_limit = pymunk.RotaryLimitJoint(torso_body, upper_arm_body, -1.0, 1.0)
        elbow_limit = pymunk.RotaryLimitJoint(upper_arm_body, lower_arm_body, 0, 1.4)
        space.add(shoulder, elbow, shoulder_limit, elbow_limit)
        joints += [shoulder, elbow, shoulder_limit, elbow_limit]

    # الأرجل
    leg_size = (20, 60)
    mass_leg = 2.0
    leg_offset_x = 15
    leg_offset_y = 80

    for side in [-1, 1]:
        # الفخذ
        upper_leg_body = pymunk.Body(mass_leg, pymunk.moment_for_box(mass_leg, leg_size))
        upper_leg_body.position = pos[0] + side * leg_offset_x, pos[1] + leg_offset_y + 80
        upper_leg_shape = pymunk.Poly.create_box(upper_leg_body, leg_size)
        upper_leg_shape.friction = 1.2
        space.add(upper_leg_body, upper_leg_shape)
        bodies.append(upper_leg_body)
        shapes.append(upper_leg_shape)

        # الساق
        lower_leg_body = pymunk.Body(mass_leg, pymunk.moment_for_box(mass_leg, leg_size))
        lower_leg_body.position = upper_leg_body.position[0], upper_leg_body.position[1] + 60
        lower_leg_shape = pymunk.Poly.create_box(lower_leg_body, leg_size)
        lower_leg_shape.friction = 1.2
        space.add(lower_leg_body, lower_leg_shape)
        bodies.append(lower_leg_body)
        shapes.append(lower_leg_shape)

        # مفاصل
        hip = pymunk.PivotJoint(torso_body, upper_leg_body, (pos[0] + side * 15, pos[1] + 80))
        knee = pymunk.PivotJoint(upper_leg_body, lower_leg_body, (0, 30), (0, -30))
        hip_limit = pymunk.RotaryLimitJoint(torso_body, upper_leg_body, -0.7, 1.0)
        knee_limit = pymunk.RotaryLimitJoint(upper_leg_body, lower_leg_body, 0, 1.5)
        space.add(hip, knee, hip_limit, knee_limit)
        joints += [hip, knee, hip_limit, knee_limit]

    return bodies, shapes, joints

# رسم مخصص آمن
def draw_human(shapes):
    for shape in shapes:
        body = shape.body
        if isinstance(shape, pymunk.Circle):
            pygame.draw.circle(screen, (200, 200, 200), (int(body.position.x), int(body.position.y)), int(shape.radius))
        elif isinstance(shape, pymunk.Poly):
            verts = shape.get_vertices()
            verts_world = [body.local_to_world(v) for v in verts]
            points = [(int(v.x), int(v.y)) for v in verts_world]
            pygame.draw.polygon(screen, (180, 180, 255), points)

# إنشاء الجسم
human_bodies, human_shapes, human_joints = create_human((WIDTH // 2, HEIGHT // 4))

# تحكم بالسحب
dragging_body = None
dragging_joint = None

# الحلقة الرئيسية
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                pos = event.pos
                for body in human_bodies:
                    for shape in body.shapes:
                        if shape.point_query(pos).distance < 0:
                            dragging_body = body
                            dragging_joint = pymunk.PivotJoint(space.static_body, body, pos, body.world_to_local(pos))
                            dragging_joint.max_force = 50000
                            space.add(dragging_joint)
                            break
                    if dragging_joint:
                        break

        elif event.type == pygame.MOUSEBUTTONUP:
            if dragging_joint:
                space.remove(dragging_joint)
                dragging_joint = None
                dragging_body = None

    if dragging_joint:
        dragging_joint.anchor_a = pygame.mouse.get_pos()

    screen.fill((30, 30, 40))
    space.step(1 / 60)
    draw_human(human_shapes)

    text = font.render("اسحب الشخصية بالماوس أو اللمس", True, (255, 255, 255))
    screen.blit(text, (10, 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()