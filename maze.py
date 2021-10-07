import harfang as hg
import math
import random

hg.InputInit()
hg.WindowSystemInit()

res_x, res_y = 1280, 720
win = hg.RenderInit('Harfang - Maze', res_x, res_y, hg.RF_VSync | hg.RF_MSAA8X)

res = hg.PipelineResources()
pipeline = hg.CreateForwardPipeline()

keyboard = hg.Keyboard()
mouse = hg.Mouse()

# access to compiled resources
hg.AddAssetsFolder('resources_compiled')
prg_ref = hg.LoadPipelineProgramRefFromAssets('core/shader/pbr.hps', res, hg.GetForwardPipelineInfo())
mat_ground = hg.CreateMaterial(prg_ref, 'uBaseOpacityColor', hg.Vec4I(40, 131, 75), 'uOcclusionRoughnessMetalnessColor', hg.Vec4(0.71, 0.51, 0.51))
mat_maze = hg.CreateMaterial(prg_ref, 'uBaseOpacityColor', hg.Vec4I(230, 20, 25), 'uOcclusionRoughnessMetalnessColor', hg.Vec4(1, 1, 1))
mat_spheres = hg.CreateMaterial(prg_ref, 'uBaseOpacityColor', hg.Vec4I(255, 71, 75), 'uOcclusionRoughnessMetalnessColor', hg.Vec4(1, 0.5, 0.1))


# 2D drawing helpers
vtx_layout = hg.VertexLayoutPosFloatNormUInt8()

sphere_mdl = hg.CreateSphereModel(vtx_layout, 1.5, 12, 24)
sphere_ref = res.AddModel('sphere', sphere_mdl)

# setup game world
scene = hg.Scene()

scene.canvas.color = hg.ColorI(37, 130, 135)
scene.environment.ambient = hg.ColorI(34, 20, 25)
mdl_ref = res.AddModel('ground', hg.CreateCubeModel(vtx_layout, 400, 0.1, 400))
hg.CreatePhysicCube(scene, hg.Vec3(400, 0.1, 400), hg.TranslationMat4(hg.Vec3(0, 0, 0)), mdl_ref, [mat_ground], 0)

lgt = hg.CreateLinearLight(scene, hg.TransformationMat4(hg.Vec3(0, 40, 0), hg.Deg3(19, 59, 0)), hg.Color(1.5, 0.9, 1.2, 1), hg.Color(1.5, 0.9, 1.2, 1), 10, hg.LST_Map, 0.002, hg.Vec4(8, 20, 40, 120))
back_lgt = hg.CreatePointLight(scene, hg.TranslationMat4(hg.Vec3(1000, 200, 1000)), 100, hg.Color(0.8, 0.5, 0.4, 1), hg.Color(0.8, 0.5, 0.4, 1), 0)

camera_node = hg.CreateCamera(scene, hg.TransformationMat4(hg.Vec3(0, 550, 0), hg.Deg3(0, 0, 0)), 0.01, 1000)

scene.SetCurrentCamera(camera_node)

clocks = hg.SceneClocks()

			# setup physics
physics = hg.SceneNewtonPhysics()
physics.SceneCreatePhysicsFromAssets(scene)
physics_step = hg.time_from_sec_f(1 / 50)


# input devices and fps controller states
keyboard = hg.Keyboard()
mouse = hg.Mouse()

#maze generation
def create_maze():
    maze_wall_ref = res.AddModel('mazewall', hg.CreateCubeModel(vtx_layout, 0.3, 50, 400))
    #create side walls
    physics.NodeCreatePhysicsFromAssets(hg.CreatePhysicCube(scene, hg.Vec3(0.3, 50, 400), hg.TranslationMat4(hg.Vec3(-200, 25, 0)), maze_wall_ref, [mat_ground], 0))
    physics.NodeCreatePhysicsFromAssets(hg.CreatePhysicCube(scene, hg.Vec3(0.3, 50, 400), hg.TranslationMat4(hg.Vec3(200, 25, 0)), maze_wall_ref, [mat_ground], 0))
    physics.NodeCreatePhysicsFromAssets(hg.CreatePhysicCube(scene, hg.Vec3(0.3, 50, 400), hg.TransformationMat4(hg.Vec3(0, 25, 200), hg.Deg3(0, 90, 0)), maze_wall_ref, [mat_ground], 0))
    physics.NodeCreatePhysicsFromAssets(hg.CreatePhysicCube(scene, hg.Vec3(0.3, 50, 400), hg.TransformationMat4(hg.Vec3(0, 25, -200), hg.Deg3(0, 90, 0)), maze_wall_ref, [mat_ground], 0))
    # main maze walls (30% chance to spawn a cube on each cube placement - 101x101 grid)
    for i in range(101):
        for x in range(101):
            a=random.randrange(0,100)
            if a < 30:
                maze_cube_ref = res.AddModel('mazecube', hg.CreateCubeModel(vtx_layout, 4, 10, 4))
                physics.NodeCreatePhysicsFromAssets(hg.CreatePhysicCube(scene, hg.Vec3(4, 10, 4), hg.TransformationMat4(hg.Vec3(-200+i*4, 5, -200+x*4), hg.Deg3(0, 0, 0)), maze_cube_ref, [mat_maze], 0))

create_maze()

ball = hg.CreatePhysicSphere(scene, 1.5, hg.TranslationMat4(hg.Vec3(190, 15, 190)), sphere_ref, [mat_spheres], 1)
physics.NodeCreatePhysicsFromAssets(ball)

# game loop
while not keyboard.Down(hg.K_Escape):
	# update mouse/keyboard devices
	keyboard.Update()
	mouse.Update()

	dt = hg.TickClock()  # tick clock, retrieve elapsed clock since last call

	# compute ratio corrected normalized mouse position
	mouse_x, mouse_y = mouse.X(), mouse.Y()

	aspect_ratio = hg.ComputeAspectRatioX(res_x, res_y)
	mouse_x_normd, mouse_y_normd = (mouse_x / res_x - 0.5) * aspect_ratio.x, (mouse_y / res_y - 0.5) * aspect_ratio.y

	# ball movement (forwards - backwards - right - left)
	vec3_ball_velocity = physics.GetNodeLinearVelocity(ball)
	vel_wanted = rot_wanted = hg.Vec3(0, 0, 0)
	maxvel = 40 if keyboard.Down(hg.K_LShift) else 20
	if keyboard.Down(hg.K_Up):
		vel_wanted = hg.Vec3(0, 0, maxvel)
		rot_wanted = hg.Deg3(0, 0, 0)
	if keyboard.Down(hg.K_Down):
		vel_wanted = hg.Vec3(0, 0, -maxvel)
		rot_wanted = hg.Deg3(0, 180, 0)
	if keyboard.Down(hg.K_Right):
		vel_wanted = hg.Vec3(maxvel, 0, 0)
		rot_wanted = hg.Deg3(0, 90, 0)
	if keyboard.Down(hg.K_Left):
		vel_wanted = hg.Vec3(-maxvel, 0, 0)
		rot_wanted =hg.Deg3(0, 270, 0)
	vel_to_apply = vel_wanted - vec3_ball_velocity
	if(keyboard.Down(hg.K_Up) or keyboard.Down(hg.K_Down) or keyboard.Down(hg.K_Left) or keyboard.Down(hg.K_Right)):
		physics.NodeAddImpulse(ball, vel_to_apply, hg.GetTranslation(ball.GetTransform().GetWorld()), physics_step)

	camera_node.GetTransform().SetPos(hg.GetT(ball.GetTransform().GetWorld()))
	camera_node.GetTransform().SetRot(rot_wanted)
	# update scene and submit it to render pipeline
	hg.SceneUpdateSystems(scene, clocks, dt, physics, physics_step, 1)
	view_id = 0
	view_id, passes_id = hg.SubmitSceneToPipeline(view_id, scene, hg.IntRect(0, 0, int(res_x), int(res_y)), True, pipeline, res)

	# end of frame
	hg.Frame()
	hg.UpdateWindow(win)


hg.RenderShutdown()
hg.DestroyWindow(win)

hg.WindowSystemShutdown()
hg.InputShutdown()
