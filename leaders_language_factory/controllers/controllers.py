# -*- coding: utf-8 -*-
# from odoo import http


# class LeadersLanguageFactory(http.Controller):
#     @http.route('/leaders_language_factory/leaders_language_factory', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/leaders_language_factory/leaders_language_factory/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('leaders_language_factory.listing', {
#             'root': '/leaders_language_factory/leaders_language_factory',
#             'objects': http.request.env['leaders_language_factory.leaders_language_factory'].search([]),
#         })

#     @http.route('/leaders_language_factory/leaders_language_factory/objects/<model("leaders_language_factory.leaders_language_factory"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('leaders_language_factory.object', {
#             'object': obj
#         })

