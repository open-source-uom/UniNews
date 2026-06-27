def set_app_info(*args):
	pass

class BaseProvider:
	def news(self, *args, **kw):
		return None
	
	def topic(self, *args, **kw):
		return None

	def headline(self, *args, **kw):
		return None

	def topstory(self, *args, **kw):
		return None

	def get_result_mapping(self):
		return None

	def get_article_mapping(self):
		return None

	def get_language_mapping(self):
		return None

	def get_country_mapping(self):
		return None

	def get_category_mapping(self):
		return None
