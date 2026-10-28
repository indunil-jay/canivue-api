
import torch
import torch.nn as nn

from behaviour_cnn_lstm import BehaviourCNNLSTM


def main():
    torch.manual_seed(42)

    model = BehaviourCNNLSTM(
        input_channels=6,
        num_classes=5,
    )

    # Eight artificial windows for an architecture test.
    # These are not real sensor recordings.
    dummy_X = torch.randn(8, 256, 6)

    # Artificial class indices for testing the loss calculation.
    dummy_y = torch.randint(0, 5, (8,))

    print("BEHAVIOUR CNN-LSTM ARCHITECTURE TEST")
    print("=" * 45)

    print("Input shape:", tuple(dummy_X.shape))

    # Test the forward pass.
    model.eval()

    with torch.no_grad():
        output = model(dummy_X)

    print("Output shape:", tuple(output.shape))
    print("All outputs finite:", torch.isfinite(output).all().item())

    # Confirm the expected output dimensions.
    assert output.shape == (8, 5)
    assert torch.isfinite(output).all()

    # Test that gradients can flow through the model.
    model.train()
    model.zero_grad()

    output = model(dummy_X)

    loss = nn.CrossEntropyLoss()(output, dummy_y)
    loss.backward()

    gradients_exist = any(
        parameter.grad is not None
        for parameter in model.parameters()
        if parameter.requires_grad
    )

    assert gradients_exist

    parameter_count = sum(
        parameter.numel()
        for parameter in model.parameters()
        if parameter.requires_grad
    )

    print("Dummy loss:", round(loss.item(), 4))
    print("Trainable parameters:", parameter_count)
    print("Gradient test passed:", gradients_exist)
    print("\nArchitecture test PASSED.")


if __name__ == "__main__":
    main()
