
Step: self.n_calls=62

self.num_timesteps=62

self.locals={'self': <stable_baselines3.ppo.ppo.PPO object at 0x7fa08603d0>,
                'total_timesteps': 4000,
                'callback': <__main__.CustomCallback object at 0x7fa0860640>,
                'log_interval': 1,
                'eval_env': None,
                'eval_freq': -1,
                'n_eval_episodes': 5,
                'tb_log_name': 'PPO103',
                'eval_log_path': None,
                'reset_num_timesteps': False,
                'iteration': 0,
                'env': <stable_baselines3.common.vec_env.dummy_vec_env.DummyVecEnv object at 0x7fa082aca0>,
                'rollout_buffer': <stable_baselines3.common.buffers.RolloutBuffer object at 0x7fa0860250>,
                'n_rollout_steps': 2048,
                'n_steps': 61,
                'obs_tensor': tensor([[ 0.6346,  0.0000,  0.9834, -0.1812,  0.0000]]),
                'actions': array([52]),
                'values': tensor([[0.5509]]),
                'log_probs': tensor([-4.7900]),
                'clipped_actions': array([52]),
                'new_obs': array([[ 0.6220353 ,  0. ,  0.98456436, -0.17502306,  1.5915494 ]], dtype=float32),
                'rewards': array([0.08363633], dtype=float32),
                'dones': array([False]),
                'infos': [{}],
                'idx': 0,
                'done': False}


self.globals={
                    '__name__': 'stable_baselines3.common.on_policy_algorithm',
                    '__doc__': None, '__package__': 'stable_baselines3.common',
                    '__loader__': <_frozen_importlib_external.SourceFileLoader object at 0x7fad6f7550>,
                    '__spec__': ModuleSpec(name='stable_baselines3.common.on_policy_algorithm',
                    loader=<_frozen_importlib_external.SourceFileLoader object at 0x7fad6f7550>,
                    origin='/home/serge/.local/lib/python3.9/site-packages/stable_baselines3/common/on_policy_algorithm.py'),
                    '__file__': '/home/serge/.local/lib/python3.9/site-packages/stable_baselines3/common/on_policy_algorithm.py',
                    '__cached__': '/home/serge/.local/lib/python3.9/site-packages/stable_baselines3/common/__pycache__/on_policy_algorithm.cpython-39.pyc',
                    '__builtins__': {'__name__': 'builtins',
                    '__doc__': "Built-in functions, exceptions, and other objects.\n\nNoteworthy: None is the `nil' object; Ellipsis represents `...' in slices.",
                    '__package__': '',
                    '__loader__': <class '_frozen_importlib.BuiltinImporter'>,
                    '__spec__': ModuleSpec(name='builtins',
                    loader=<class '_frozen_importlib.BuiltinImporter'>,
                    origin='built-in'),
                    '__build_class__': <built-in function __build_class__>,
                    '__import__': <built-in function __import__>,
                    'abs': <built-in function abs>,
                    'all': <built-in function all>,
                    'any': <built-in function any>,
                    'ascii': <built-in function ascii>,
                    'bin': <built-in function bin>,
                    'breakpoint': <built-in function breakpoint>,
                    'callable': <built-in function callable>,
                    'chr': <built-in function chr>,
                    'compile': <built-in function compile>,
                    'delattr': <built-in function delattr>,
                    'dir': <built-in function dir>,
                    'divmod': <built-in function divmod>,
                    'eval': <built-in function eval>,
                    'exec': <built-in function exec>,
                    'format': <built-in function format>,
                    'getattr': <built-in function getattr>,
                    'globals': <built-in function globals>,
                    'hasattr': <built-in function hasattr>,
                    'hash': <built-in function hash>,
                    'hex': <built-in function hex>,
                    'id': <built-in function id>,
                    'input': <built-in function input>,
                    'isinstance': <built-in function isinstance>,
                    'issubclass': <built-in function issubclass>,
                    'iter': <built-in function iter>,
                    'len': <built-in function len>,
                    'locals': <built-in function locals>,
                    'max': <built-in function max>,
                    'min': <built-in function min>,
                    'next': <built-in function next>,
                    'oct': <built-in function oct>,
                    'ord': <built-in function ord>,
                    'pow': <built-in function pow>,
                    'print': <built-in function print>,
                    'repr': <built-in function repr>,
                    'round': <built-in function round>,
                    'setattr': <built-in function setattr>,
                    'sorted': <built-in function sorted>,
                    'sum': <built-in function sum>,
                    'vars': <built-in function vars>,
                    'None': None,
                    'Ellipsis': Ellipsis,
                    'NotImplemented': NotImplemented,
                    'False': False,
                    'True': True,
                    'bool': <class 'bool'>,
                    'memoryview': <class 'memoryview'>,
                    'bytearray': <class 'bytearray'>,
                    'bytes': <class 'bytes'>,
                    'classmethod': <class 'classmethod'>,
                    'complex': <class 'complex'>,
                    'dict': <class 'dict'>,
                    'enumerate': <class 'enumerate'>,
                    'filter': <class 'filter'>,
                    'float': <class 'float'>,
                    'frozenset': <class 'frozenset'>,
                    'property': <class 'property'>,
                    'int': <class 'int'>,
                    'list': <class 'list'>,
                    'map': <class 'map'>,
                    'object': <class 'object'>,
                    'range': <class 'range'>,
                    'reversed': <class 'reversed'>,
                    'set': <class 'set'>,
                    'slice': <class 'slice'>,
                    'staticmethod': <class 'staticmethod'>,
                    'str': <class 'str'>,
                    'super': <class 'super'>,
                    'tuple': <class 'tuple'>,
                    'type': <class 'type'>,
                    'zip': <class 'zip'>,
                    '__debug__': True,
                    'open': <built-in function open>,
                    'quit': "Use quit() or Ctrl-D (i.e. EOF) to exit",
                    'exit': "Use exit() or Ctrl-D (i.e. EOF) to exit",
                    'copyright': "Copyright (c) 2001-2021 Python Software Foundation."}

dir(self)
['__abstractmethods__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__slots__', '__str__', '__subclasshook__', '__weakref__', '_abc_impl', '_init_callback', '_on_rollout_end', '_on_rollout_start', '_on_step', '_on_training_end', '_on_training_start', 'globals', 'init_callback', 'locals', 'logger', 'model', 'n_calls', 'num_timesteps', 'on_rollout_end', 'on_rollout_start', 'on_step', 'on_training_end', 'on_training_start', 'parent', 'stop_learn', 'training_env', 'update_child_locals', 'update_locals', 'verbose']

dir(self.training_env)
['__abstractmethods__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__slots__', '__str__', '__subclasshook__', '__weakref__', '_abc_impl', '_get_indices', '_get_target_envs', '_obs_from_buf', '_save_obs', 'action_space', 'actions', 'buf_dones', 'buf_infos', 'buf_obs', 'buf_rews', 'close', 'env_is_wrapped', 'env_method', 'envs', 'get_attr', 'get_images', 'getattr_depth_check', 'keys', 'metadata', 'num_envs', 'observation_space', 'render', 'reset', 'seed', 'set_attr', 'step', 'step_async', 'step_wait', 'unwrapped']
