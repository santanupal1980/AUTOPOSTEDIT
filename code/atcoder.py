import tensorflow as tf

def create(model, config):
	dim_v, dim_i, dim_d, dim_t, dim_b, dim_m, dim_p = config.getint('vocab'), config.getint('wvec'), config.getint('depth'), config.getint('steps'), config.getint('batch'), config.getint('memory'), config.getint('predictions')
	lrate_ms, dstep_ms, drate_ms, optim_ms = config.getfloat('lrate'), config.getint('dstep'), config.getfloat('drate'), getattr(tf.train, config.get('optim'))

	with tf.name_scope('decoder'):
		with tf.name_scope('input'):
			model['dh_%i_%i' %(dim_d - 1, -1)] = tf.Variable(tf.truncated_normal([1, dim_i], stddev = 1.0 / dim_i), name = 'dh_%i_%i' %(dim_d -1, -1)) # consider starting with all zeros

		with tf.name_scope('label'):
			for ii in xrange(dim_t):
				model['dyi_%i' %ii] = tf.placeholder(tf.int32, [dim_b], name = 'dyi_%i' %ii)
				model['dy_%i' %ii] = tf.add(tf.nn.embedding_lookup(model['We'], model['dyi_%i' %ii]), model['Be'], name = 'dy_%i' %ii)

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
				model['dWc_%i' %i] = tf.Variable(tf.truncated_normal([dim_i, dim_i], stddev = 1.0 / dim_i), name = 'dWc_' + str(i))
				model['dBc_%i' %i] = tf.Variable(tf.truncated_normal([1, dim_i], stddev = 1.0 / dim_i), name = 'dBc_' + str(i))

			with tf.name_scope('attention_%i' %i):
				model['dWa_%i' %i] = tf.Variable(tf.truncated_normal([dim_i, dim_i], stddev = 1.0 / dim_i), name = 'dWa_%i' %i)
				model['dBa_%i' %i] = tf.Variable(tf.truncated_normal([dim_t, 1], stddev = 1.0 / dim_t), name = 'dBa_%i' %i)

			with tf.name_scope('hidden_%i' %i):
				model['dWx_%i' %i] = tf.Variable(tf.truncated_normal([dim_i, dim_i], stddev = 1.0 / dim_i), name = 'dWx_%i' %i)
				model['dWz_%i' %i] = tf.Variable(tf.truncated_normal([dim_i, dim_i], stddev = 1.0 / dim_i), name = 'dWz_%i' %i)
				model['dBz_%i' %i] = tf.Variable(tf.truncated_normal([1, dim_i], stddev = 1.0 / dim_i), name = 'dBz_%i' %i)

			with tf.name_scope('memory_%i' %i):
				model['dmi_%i' %i] = tf.reshape([model['ec_%i_%i' %(i, ii)] for ii in xrange(dim_t - dim_m, dim_t)], [dim_t, dim_b, dim_i], name = 'dmi_%i' %i)
				model['dm_%i' %i] = tf.transpose(model['dmi_%i' %i], [1, 0, 2], name = 'dm_%i' %i)

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
					model['dcc_%i_%i' %(i, ii)] = model['ec_%i_%i' %(i, dim_t - 1)] if ii == 0 else model['dc_%i_%i' %(i, ii - 1)] # consider starting with all zeros
					model['dc_%i_%i' %(i, ii)] = tf.add(tf.mul(model['df_%i_%i' %(i, ii)], model['dcc_%i_%i' %(i, ii)]), tf.mul(model['di_%i_%i' %(i, ii)], tf.nn.tanh(tf.add(tf.matmul(model['dx_%i_%i' %(i, ii)], model['dWc_%i' %i]), model['dBc_%i' %i]))), name = 'dc_%i_%i' %(i, ii))

				with tf.name_scope('attention_%i_%i' %(i, ii)):
					model['dat_%i_%i' %(i, ii)] = tf.nn.softmax(tf.add(tf.reshape(tf.transpose(tf.batch_matmul(model['dm_%i' %i], tf.reshape(tf.transpose(tf.matmul(model['dWa_%i' %i], tf.transpose(model['dc_%i_%i' %(i, ii)]))), [dim_b, dim_i, 1]))), [dim_t, dim_b]), model['dBa_%i' %i]), name = 'dat_%i_%i' %(i, ii))
					model['dcx_%i_%i' %(i, ii)] = tf.reshape(tf.batch_matmul(tf.reshape(tf.transpose(model['dat_%i_%i' %(i, ii)]), [dim_b, 1, dim_t]), model['dm_%i' %i]), [dim_b, dim_i], name = 'dcx_%i_%i' %(i, ii))

				with tf.name_scope('hidden_%i_%i' %(i, ii)):
					model['dz_%i_%i' %(i, ii)] = tf.add(tf.add(tf.matmul(model['dcx_%i_%i' %(i, ii)], model['dWx_%i' %i]), tf.matmul(model['dc_%i_%i' %(i, ii)], model['dWz_%i' %i])), model['dBz_%i' %i], name = 'dz_%i_%i' %(i, ii))

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
				model['dp_%i' %ii] = tf.nn.top_k(tf.matmul(model['dh_%i' %ii], model['We'], transpose_b = True), dim_p, name = 'dp_%i' %ii)

	model['gsdms'] = tf.Variable(0, trainable = False, name = 'gsdms')
	model['lrdms'] = tf.train.exponential_decay(lrate_ms, model['gsdms'], dstep_ms, drate_ms, staircase = False, name = 'lrdms')
	model['tdms'] = optim_ms(model['lrdms']).minimize(model['dms'], global_step = model['gsdms'], name = 'tdms')

	return model