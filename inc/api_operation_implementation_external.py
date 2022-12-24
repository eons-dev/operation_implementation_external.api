import os
import logging
import apie
import eons
import requests
from urllib.parse import urlparse
from api_operation_implementation import operation_implementation

# External Endpoints make a request to another server and return the result.
class operation_implementation_external(operation_implementation):
	def __init__(this, name="external implementation", implements=eons.INVALID_NAME()):
		super().__init__(name, implements)

		this.requiredKWArgs.append('url')
		
		this.optionalKWArgs['method'] = "get"
		this.optionalKWArgs['authenticator'] = ""
		this.optionalKWArgs['query_map'] = {} #get parameters
		this.optionalKWArgs['data_map'] = {} #request body
		this.optionalKWArgs['headers'] = None #None => request.headers; {} => {}
		this.optionalKWArgs['data'] = {}
		this.optionalKWArgs['files'] = {}
		this.optionalKWArgs['decode'] = 'ascii'

		this.clobberContent = False

		this.externalRequest = {}
		this.externalResponse = None

	# Required Endpoint method. See that class for details.
	def GetHelpText(this):
		return '''\
Make a request to an external web endpoint.
This will:
	1. Map data from variables into fields for the request body per the 'data_map'
	2. Make an internal request dictionary called 'externalRequest'
	3. If possible, authenticate that request via the Authenticator set in 'authenticator'
	4. If the request was authenticated, the request will be made and the result will be stored in the response.

When sending the response, the result is decoded as ascii. This means sending binary files will require a base64 encoding, etc.
'''

	def MapData(this):
		this.path = urlparse(this.url).path[1:]

		if (this.data_map):
			for key, val in this.data_map.items():
				# this.data.update({key: eons.util.GetAttr(this,val)})
				value = this.Fetch(val, None)
				if (value is None):
					continue
				this.data.update({key: value})

		if (this.query_map):
			this.url += '?'
			for key, val in this.query_map.items():
				# this.url += f"{key}={eons.util.GetAttr(this,val)}&"
				value = this.Fetch(val, None)
				if (value is None):
					continue
				this.url += f"{key}={value}&"
			this.url = this.url[:-1] #trim the last "&"

	def ConstructRequest(this):
		this.externalRequest = {
			'method': this.method,
			'url': this.url,
			'headers': this.headers,
			'data': this.data,
			'files': this.files
		}
		if (this.headers is None):
			this.externalRequest['headers'] = this.request.headers

	def AuthenticateRequest(this):
		if (not this.authenticator):
			return True

		# TODO: cache auth??
		this.auth = this.executor.GetRegistered(this.authenticator, "auth")
		return this.auth(executor=this.executor, path=this.path, request=this.externalRequest, precursor=this)

	def MakeRequest(this):
		logging.debug(f"Making request: {this.externalRequest}")
		this.externalResponse = requests.request(**this.externalRequest)

	def PrepareResponse(this):
		this.response.code = this.externalResponse.status_code
		this.response.headers = this.externalResponse.headers
		if (this.decode):
			this.response.content.string = this.externalResponse.content.decode(this.decode)
		else:
			this.response.content.string = this.externalResponse.content

	# Required Endpoint method. See that class for details.
	def MakeExternalCall(this):
		this.MapData()
		this.ConstructRequest()
		if (not this.AuthenticateRequest()):

			this.response.content.string, this.response.code = this.auth.Unauthorized(this.path)
			#TODO: Headers?
			return
		this.MakeRequest()
		this.PrepareResponse()
