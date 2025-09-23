import aws_cdk as cdk
from src.model.project import Project
from src.stack.app_stack import AppStack


def add_name_tag(scope):  # noqa: ANN001, ANN201
    """Recursively add 'Name' tag to all resources in the scope."""
    for child in scope.node.children:
        if cdk.Resource.is_resource(child):
            cdk.Tags.of(child).add("Name", child.node.path.replace("/", "-"))
        add_name_tag(child)


# Initialize the CDK application
app = cdk.App()

# Define the project metadata
project = Project()

# 統合アプリケーションスタック
app_stack = AppStack(
    scope=app,
    construct_id=f"{project.camel_case_name}App",
    project=project,
    env=cdk.Environment(
        region="ap-northeast-1",
    ),
)

cdk.Tags.of(app).add("Project", project.name)
cdk.Tags.of(app).add("ManagedBy", "cdk")
add_name_tag(app)
app.synth()
