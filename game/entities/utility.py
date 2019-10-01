import peachy

# Entity constants
INVINCIBILITY_DURATION = 20
GRAVITY = 0.2
MAX_GRAVITY = 6


def collision_resolution(entity, temp_x, temp_y):

    # TODO fix spacing. for some reason certain collisions allow for a gap
    # in space etc

    vel_x = entity.velocity_x
    vel_y = entity.velocity_y

    collisions = entity.collides_solid(temp_x, temp_y)
    for collision in collisions:

        if not entity.collides(collision, temp_x, temp_y):
            continue

        elif collision.member_of('solid') and collision.slanted:

            # TODO fix snag at top of slope

            left = collision.intersection(temp_x)
            right = collision.intersection(temp_x + entity.width)

            if temp_y + entity.height > left or temp_y + entity.height > right:
                if collision.y < left < right:
                    temp_y = left - entity.height
                elif collision.y < right < left:
                    temp_y = right - entity.height
                else:
                    temp_y = collision.y - entity.height
                vel_y = 0

        elif collision.member_of('platform'):
            if vel_y < 0:
                collision.solid = False
            elif not entity.collides(collision, temp_x, entity.y):
                temp_y = collision.y - entity.height
                vel_y = 0

        elif not entity.collides(collision, temp_x, entity.y):
            if temp_y - entity.height - vel_y < collision.y and vel_y > 0:
                temp_y = collision.y - entity.height
            elif temp_y + vel_y > collision.y - collision.height and vel_y < 0:
                temp_y = collision.y + collision.height
            vel_y = 0

        elif not entity.collides(collision, entity.x, temp_y):
            if temp_x - entity.width - vel_x < collision.x and vel_x > 0:
                temp_x = collision.x - entity.width
            elif temp_x + vel_x > collision.x - collision.width and vel_x < 0:
                temp_x = collision.x + collision.width
            vel_x = 0

        else:
            temp_x = entity.x
            temp_y = entity.y
            vel_x = 0
            vel_y = 0
            break

    collision_occurred = len(collisions) > 0

    return collision_occurred, temp_x, temp_y, vel_x, vel_y


def draw_message(player, message):
    HEIGHT = 64
    y = 0

    if player.y + player.height < HEIGHT:
        y = peachy.PC.height - HEIGHT

    peachy.graphics.set_color(0, 30, 60)
    peachy.graphics.draw_rect(0, y, peachy.PC.width, HEIGHT)
    peachy.graphics.set_color(255, 255, 255)
    peachy.graphics.draw_text(message, 8, y + 8)


def get_line_segments(entity):
    return [[entity.x, entity.y, entity.width, 0],
            [entity.x + entity.width, entity.y, 0, entity.height],
            [entity.x + entity.width, entity.y + entity.height, -entity.width,
            0],
            [entity.x, entity.y + entity.height, 0, -entity.height]]


def line_line_collision(lineA1, lineA2, lineB1, lineB2):
    denominator = ((lineB2[1] - lineB1[1]) * (lineA2[0] - lineA1[0])) - \
                  ((lineB2[0] - lineB1[0]) * (lineA2[1] - lineA1[1]))

    if denominator == 0:
        return False
    else:
        ua = (((lineB2[0] - lineB1[0]) * (lineA1[1] - lineB1[1])) -
              ((lineB2[1] - lineB1[1]) * (lineA1[0] - lineB1[0]))) / denominator

        ub = (((lineA2[0] - lineA1[0]) * (lineA1[1] - lineB1[1])) -
              ((lineA2[1] - lineA1[1]) * (lineA1[0] - lineB1[0]))) / denominator

        if (ua < 0) or (ua > 1) or (ub < 0) or (ub > 1):
            return False
        return True


def raycast(sx, sy, ex, ey, obstructions):
    lineA1 = (sx, sy)
    lineA2 = (ex, ey)

    for obstruction in obstructions:
        segments = []
        try:
            segments = obstruction.segments
        except(AttributeError, IndexError):
            segments = get_line_segments(obstruction)

        for segment in segments:
            lineB1 = (segment[0], segment[1])
            lineB2 = (segment[0] + segment[2], segment[1] + segment[3])
            if line_line_collision(lineA1, lineA2, lineB1, lineB2):
                return False
    return True


def solid_above(entity, x, y):
    return entity.collides_solid(x, y - 1)


def solid_below(entity, x, y):
    return entity.collides_solid(x, y + 1)


def solid_left(entity, x, y):
    return entity.collides_solid(x - 1, y)


def solid_right(entity, x, y):
    return entity.collides_solid(x + 1, y)


def string_escape(string):
    # Convert raw string to unicode string
    return bytes(string, 'utf-8').decode('unicode-escape')


def xcollides_solid(entity, x, y):
    # collision detection procedure that includes slanted solids
    collisions_raw = entity.collides_solid(x, y)
    collisions = []
    for collision in collisions_raw:
        if collision.member_of('solid') and collision.slanted:
            left = collision.intersection(x)
            right = collision.intersection(x + entity.width)

            if y + entity.height > left or \
               y + entity.height > right:
                collisions.append(collision)
        else:
            collisions.append(collision)
    return collisions


def knockback(entity, attacker, force):
    temp_x = entity.x
    temp_y = entity.y
    if attacker.x < entity.x:
        entity.velocity_x = force
    elif attacker.x > entity.x:
        entity.velocity_x = -force

    temp_x += entity.velocity_x * 2
    if xcollides_solid(entity, temp_x, entity.y):
        temp_x = entity.x
        entity.velocity_x = 0

    if attacker.y < entity.y:
        entity.velocity_y = force / 2
    elif attacker.y > entity.y:
        entity.velocity_y = -force / 2

    temp_y += entity.velocity_y * 2
    if xcollides_solid(entity, entity.x, temp_y):
        temp_y = entity.y
        entity.velocity_y = 0

    _, entity.x, entity.y, entity.velocity_x, entity.velocity_y = \
        collision_resolution(entity, temp_x, temp_y)
