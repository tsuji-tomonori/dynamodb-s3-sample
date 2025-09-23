from aws_cdk import App, Aspects, assertions
from cdk_nag import AwsSolutionsChecks
from src.model.project import Project
from src.stack.app_stack import AppStack


def test_cdk_nag():
    app = App()
    project = Project()
    stack = AppStack(app, "AppStack", project=project)
    Aspects.of(stack).add(AwsSolutionsChecks(verbose=True))

    # ルール ID で ERROR / WARN を抽出
    errors = assertions.Annotations.from_stack(stack).find_error(
        "*", assertions.Match.string_like_regexp(r"AwsSolutions-.*")
    )
    assert errors == [], f"CDK Nag Errors: {errors}"

    warns = assertions.Annotations.from_stack(stack).find_warning(
        "*", assertions.Match.string_like_regexp(r"AwsSolutions-.*")
    )
    assert warns == [], f"CDK Nag Warnings: {warns}"
