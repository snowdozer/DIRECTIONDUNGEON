ACCEL = 5.71428

speed = 0
distance = 0
seconds = 0

for second in range(0, 20):
    seconds += 1
    speed += ACCEL
    distance += speed

    print("Time: %2i Speed: %6.2f, Distance: %7.2f" % (seconds, speed, distance))