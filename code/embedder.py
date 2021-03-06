import tensorflow as tf

def create(config, scope = 'embedder'):
	dim_v, dim_i = config.getint('vocab'), config.getint('wvec')
	model = dict()

	with tf.name_scope(scope):
		model['We'] = tf.Variable(tf.truncated_normal([dim_v, dim_i], stddev = 1.0 / dim_i), name = 'We')
		model['Be'] = tf.Variable(tf.truncated_normal([1, dim_i], stddev = 1.0 / dim_i), name = 'Be')

	return model
