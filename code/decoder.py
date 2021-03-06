import tensorflow as tf

def create(embedder, encoder1, encoder2, combiner, config, scope = 'decoder'):
	dim_v, dim_i, dim_d, dim__d_, dim_t, dim_b, dim_p = config.getint('vocab'), config.getint('wvec'), config.getint('depth'), config.getint('_depth_'), config.getint('steps'), config.getint('batch'), config.getint('predictions')
	biencoder, lrate_ms, dstep_ms, drate_ms, optim_ms = config.getboolean('biencoder'), config.getfloat('lrate'), config.getint('dstep'), config.getfloat('drate'), getattr(tf.train, config.get('optim'))
	model = dict()

	with tf.name_scope(scope):
		with tf.name_scope('input'):
			model['dh_%i_%i' %(dim_d - 1, -1)] = combiner['cy_%i' %(dim__d_ - 1)]

		with tf.name_scope('label'):
			for ii in xrange(dim_t):
				model['dyi_%i' %ii] = tf.placeholder(tf.int32, [dim_b], name = 'dyi_%i' %ii)
				model['dy_%i' %ii] = tf.add(tf.nn.embedding_lookup(embedder['We'], model['dyi_%i' %ii]), embedder['Be'], name = 'dy_%i' %ii)

		for i in xrange(dim_d):
			with tf.name_scope('inputgate_%i' %i):
				model['dWi_%i' %i] = tf.Variable(tf.truncated_normal([dim_i, dim_i], stddev = 1.0 / dim_i), name = 'dWi_%i' %i)
				model['dBi_%i' %i] = tf.Variable(tf.truncated_normal([1, dim_i], stddev = 1.0 / dim_i), name = 'dBi_%i' %i)

			with tf.name_scope('forgetgate_%i' %i):
				model['dWf_%i' %i] = tf.Variable(tf.truncated_normal([dim_i, dim_i], stddev = 1.0 / dim_i), name = 'dWf_%i' %i)
				model['dBf_%i' %i] = tf.Variable(tf.truncated_normal([1, dim_i], stddev = 1.0 / dim_i), name = 'dBf_%i' %i)

			with tf.name_scope('outputgate_%i' %i):
				model['dWo_%i' %i] = tf.Variable(tf.truncated_normal([dim_i, dim_i], stddev = 1.0 / dim_i), name = 'dWo_%i' %i)
				model['dBo_%i' %i] = tf.Variable(tf.truncated_normal([1, dim_i], stddev = 1.0 / dim_i), name = 'dBo_%i' %i)

			with tf.name_scope('cellstate_%i' %i):
				model['dWc_%i' %i] = tf.Variable(tf.truncated_normal([dim_i, dim_i], stddev = 1.0 / dim_i), name = 'dWc_%i' %i)
				model['dBc_%i' %i] = tf.Variable(tf.truncated_normal([1, dim_i], stddev = 1.0 / dim_i), name = 'dBc_%i' %i)

			with tf.name_scope('transferstate_%i' %i):
				factor = 4 if biencoder else 2
				model['dWt_%i' %i] = tf.Variable(tf.truncated_normal([factor * dim_i, dim_i], stddev = 1.0 / dim_i), name = 'dWt_%i' %i)
				model['dBt_%i' %i] = tf.Variable(tf.truncated_normal([1, dim_i], stddev = 1.0 / dim_i), name = 'dBt_%i' %i)

			with tf.name_scope('hidden_%i' %i):
				model['dWz_%i' %i] = tf.Variable(tf.truncated_normal([dim_i, dim_i], stddev = 1.0 / dim_i), name = 'dWz_%i' %i)
				model['dBz_%i' %i] = tf.Variable(tf.truncated_normal([1, dim_i], stddev = 1.0 / dim_i), name = 'dBz_%i' %i)

			with tf.name_scope('transfer_%i_%i' %(i, dim_t - 1)):
				model['ec_%i_%i' %(i, dim_t - 1)] = tf.concat(1, [encoder1['ec_%i_%i' %(i, dim_t - 1)], encoder2['ec_%i_%i' %(i, dim_t - 1)]], name = 'ec_%i_%i' %(i, dim_t - 1))
				model['ect_%i_%i' %(i, dim_t - 1)] = tf.add(tf.matmul(model['ec_%i_%i' %(i, dim_t - 1)], model['dWt_%i' %i]), model['dBt_%i' %i], 'ect_%i_%i' %(i, dim_t - 1))


		for ii in xrange(dim_t):
			for i in xrange(dim_d):
				with tf.name_scope('input_%i_%i' %(i, ii)):
					model['dx_%i_%i' %(i, ii)] = model['dh_%i_%i' %(dim_d - 1, ii - 1)] if i == 0 else model['dh_%i_%i' %(i - 1, ii)]

				with tf.name_scope('inputgate_%i_%i' %(i, ii)):
					model['di_%i_%i' %(i, ii)] = tf.nn.sigmoid(tf.add(tf.matmul(model['dx_%i_%i' %(i, ii)], model['dWi_%i' %i]), model['dBi_%i' %i]), name = 'di_%i_%i' %(i, ii))

				with tf.name_scope('forgetgate_%i_%i' %(i, ii)):
					model['df_%i_%i' %(i, ii)] = tf.nn.sigmoid(tf.add(tf.matmul(model['dx_%i_%i' %(i, ii)], model['dWf_%i' %i]), model['dBf_%i' %i]), name = 'df_%i_%i' %(i, ii))
	
				with tf.name_scope('outputgate_%i_%i' %(i, ii)):
					model['do_%i_%i' %(i, ii)] = tf.nn.sigmoid(tf.add(tf.matmul(model['dx_%i_%i' %(i, ii)], model['dWo_%i' %i]), model['dBo_%i' %i]), name = 'do_%i_%i' %(i, ii))

				with tf.name_scope('cellstate_%i_%i' %(i, ii)):
					model['dcc_%i_%i' %(i, ii)] = model['ect_%i_%i' %(i, dim_t - 1)] if ii == 0 else model['dc_%i_%i' %(i, ii - 1)] # consider starting with all zeros
					model['dc_%i_%i' %(i, ii)] = tf.add(tf.mul(model['df_%i_%i' %(i, ii)], model['dcc_%i_%i' %(i, ii)]), tf.mul(model['di_%i_%i' %(i, ii)], tf.nn.tanh(tf.add(tf.matmul(model['dx_%i_%i' %(i, ii)], model['dWc_%i' %i]), model['dBc_%i' %i]))), name = 'dc_%i_%i' %(i, ii))

				with tf.name_scope('hidden_%i_%i' %(i, ii)):
					model['dz_%i_%i' %(i, ii)] = tf.add(tf.matmul(model['dc_%i_%i' %(i, ii)], model['dWz_%i' %i]), model['dBz_%i' %i], name = 'dz_%i_%i' %(i, ii))

				with tf.name_scope('output_%i_%i' %(i, ii)):
					model['dh_%i_%i' %(i, ii)] = tf.mul(model['do_%i_%i' %(i, ii)], tf.nn.tanh(model['dz_%i_%i' %(i, ii)]), name = 'dh_%i_%i' %(i, ii))

		with tf.name_scope('output'):
			for ii in xrange(dim_t):
				model['dh_%i' %ii] = model['dh_%i_%i' %(dim_d - 1, ii)]

		with tf.name_scope('meansquared'):
			for ii in xrange(dim_t):
				model['dms_%i' %ii] = tf.select(tf.equal(model['dyi_%i' %ii], tf.zeros([dim_b], tf.int32)), tf.zeros([dim_b], tf.float32), tf.reduce_sum(tf.square(tf.sub(model['dy_%i' %ii], model['dh_%i' %ii])), [1]), name = 'dms_%i' %ii)
			model['dms'] = tf.reduce_sum(tf.add_n([model['dms_%i' %ii] for ii in xrange(dim_t)]), name = 'dms')
			model['sdms'] = tf.scalar_summary(model['dms'].name, model['dms'])

		with tf.name_scope('predict'):
			for ii in xrange(dim_t):
				model['dp_%i' %ii] = tf.nn.top_k(tf.matmul(model['dh_%i' %ii], embedder['We'], transpose_b = True), dim_p, name = 'dp_%i' %ii)

	model['gsdms'] = tf.Variable(0, trainable = False, name = 'gsdms')
	model['lrdms'] = tf.train.exponential_decay(lrate_ms, model['gsdms'], dstep_ms, drate_ms, staircase = False, name = 'lrdms')
	model['tdms'] = optim_ms(model['lrdms']).minimize(model['dms'], global_step = model['gsdms'], name = 'tdms')

	return model
