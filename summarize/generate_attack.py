from .attack import get_grad, fgsm_attack, mi_fgsm_attack
import torch
import torch.nn.functional as F


def generate_attack(model, criterion, attack, test_loader, test_dataset, epsilon, device):
    '''
    return: accuracy, attack instance generated, and laebl 
    '''
    
    # Accuracy counter
    correct = 0
    adv_examples = []

    # Loop over all examples in test set
    for data, target in test_loader:
         # Send the data and label to the device
        data, target = data.to(device), target.to(device)

        data_grad, mask = get_grad(model, criterion, data, target)

        # Call Attack
        perturbed_data = attack(data, epsilon, data_grad, mask, model, criterion, data, target, device)

        # Re-classify the perturbed image
        output = model(perturbed_data)

        # Check for success
        final_pred = output.max(1, keepdim=True)[1] # get the index of the max log-probability

        # calculate correct prediction
        correct += torch.sum(torch.eq(final_pred.flatten(), target.flatten())).item()
        # Special case for saving 0 epsilon examples
        
        adv_ex = perturbed_data.squeeze().detach().cpu().numpy()
        adv_examples.append( (target.flatten().detach().cpu().numpy(), adv_ex) )
        # pred_list.append((init_pred.flatten().detach().cpu().numpy(), final_pred.flatten().detach().cpu().numpy()))
        
    label = [j for i in adv_examples for j in i[0]]
    adv_ex = [j for i in adv_examples for j in i[1]]

    # Calculate final accuracy for this epsilon
    final_acc = correct/float(len(test_dataset))
    print("Epsilon: {}\tTest Accuracy = {} / {} = {}".format(epsilon, correct, len(test_dataset), final_acc))

    # Return the accuracy and an adversarial example
    return final_acc, adv_ex, label


def generate_fgsm_attack(model, criterion, test_loader, test_dataset, epsilon, device):
    return generate_attack(model, criterion, fgsm_attack, test_loader, test_dataset, epsilon, device)


def generate_mi_fgsm_attack(model, criterion, test_loader, test_dataset, epsilon, device):
    return generate_attack(model, criterion, mi_fgsm_attack, test_loader, test_dataset, epsilon, device)


def grey_box_attack_test(model, attack_loader, device):
    '''
    attack_loader: dataloader of attack instance
    '''
    correct = 0.
    for data, target in attack_loader:

        # Send the data and label to the device
        data, target = data.to(device), target.to(device)

        # Forward pass the data through the model
        output = model(data)
        pred = output.max(1, keepdim=True)[1] # get the index of the max log-probability

        # Zero all existing gradients
        model.zero_grad()

        # calculate correct prediction
        correct += torch.sum(torch.eq(pred.flatten(), target.flatten())).item()
        # Special case for saving 0 epsilon examples

    # Calculate final accuracy for this epsilon
    final_acc = correct/float(len(attack_loader))

    # Return the accuracy and an adversarial example
    return final_acc