from ninja_extra import NinjaExtraAPI, APIController, route, router


@router('')
class SomeAPIController(APIController):
    @route.get('/example')
    def example(self):
        pass


api = NinjaExtraAPI()


@api.get("/global")
def global_op(request):
    pass


api.register_controllers(SomeAPIController)


def test_api_instance():
    assert len(api._routers) == 2  # default + extra
    for path, rtr in api._routers:
        for path_ops in rtr.path_operations.values():
            for op in path_ops.operations:
                assert op.api is api
